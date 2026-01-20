"""
Family Office Platform - Agent Manager

Orchestrates multiple AI agents, manages task routing,
and coordinates agent interactions.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Type

from flask import current_app

from app import db
from app.models import AgentTask
from app.agents.base_agent import BaseAgent, AgentResponse
from app.agents.cfa_agent import CFAAgent
from app.agents.cfp_agent import CFPAgent
from app.agents.cio_agent import CIOAgent
from app.agents.accountant_agent import AccountantAgent
from app.agents.quant_analyst import QuantAnalyst
from app.utils.exceptions import AgentError, ValidationError

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Manages and orchestrates all AI agents.

    Responsibilities:
    - Agent registration and lifecycle
    - Task routing to appropriate agents
    - Inter-agent communication
    - Result aggregation
    - Performance monitoring
    """

    # Agent registry
    AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
        'cfa': CFAAgent,
        'cfp': CFPAgent,
        'cio': CIOAgent,
        'accountant': AccountantAgent,
        'quant_risk': QuantAnalyst,
        'quant_strategy': QuantAnalyst
    }

    def __init__(self, user_id: str = None, portfolio_data: Dict[str, Any] = None):
        """
        Initialize agent manager.

        Args:
            user_id: User ID for scoping agent operations
            portfolio_data: Portfolio data for agents
        """
        self.user_id = user_id
        self.portfolio_data = portfolio_data or {}
        self._agents: Dict[str, BaseAgent] = {}

    def get_agent(self, agent_type: str) -> BaseAgent:
        """
        Get or create an agent instance.

        Args:
            agent_type: Type of agent (cfa, cfp, cio, accountant, quant_risk, quant_strategy)

        Returns:
            Agent instance

        Raises:
            ValidationError: If agent type is invalid
        """
        if agent_type not in self.AGENT_REGISTRY:
            raise ValidationError(
                f"Unknown agent type: {agent_type}. Valid types: {list(self.AGENT_REGISTRY.keys())}"
            )

        # Return cached agent if exists
        if agent_type in self._agents:
            return self._agents[agent_type]

        # Create new agent
        agent_class = self.AGENT_REGISTRY[agent_type]

        # Handle quant analyst specialty
        if agent_type == 'quant_risk':
            agent = agent_class(self.user_id, self.portfolio_data, specialty='risk_modeling')
        elif agent_type == 'quant_strategy':
            agent = agent_class(self.user_id, self.portfolio_data, specialty='strategy_development')
        else:
            agent = agent_class(self.user_id, self.portfolio_data)

        self._agents[agent_type] = agent
        return agent

    def run_analysis(
        self,
        agent_type: str,
        task_type: str = 'full_analysis',
        save_task: bool = True
    ) -> AgentResponse:
        """
        Run analysis using specified agent.

        Args:
            agent_type: Type of agent to use
            task_type: Type of analysis task
            save_task: Whether to save task to database

        Returns:
            AgentResponse with analysis results

        Raises:
            AgentError: If analysis fails
        """
        task = None

        try:
            # Create task record if saving
            if save_task:
                task = AgentTask.create_task(
                    user_id=self.user_id,
                    agent_type=agent_type,
                    task_type=task_type,
                    input_data=self.portfolio_data
                )
                db.session.add(task)
                db.session.commit()
                task.start()
                db.session.commit()

            # Get agent and run analysis
            agent = self.get_agent(agent_type)
            response = agent.analyze()

            # Update task with results
            if task:
                task.complete(
                    output_data=response.metadata,
                    recommendations=response.recommendations,
                    confidence_score=response.confidence_score,
                    reasoning=response.reasoning
                )
                db.session.commit()

            logger.info(f"Agent {agent_type} analysis completed for user {self.user_id}")
            return response

        except Exception as e:
            logger.error(f"Agent {agent_type} analysis failed: {e}")

            if task:
                task.fail(str(e))
                db.session.commit()

            raise AgentError(
                f"Analysis failed: {str(e)}",
                agent_type=agent_type
            )

    def run_all_analyses(self, save_tasks: bool = True) -> Dict[str, AgentResponse]:
        """
        Run analyses with all available agents.

        Args:
            save_tasks: Whether to save tasks to database

        Returns:
            Dictionary of agent_type -> AgentResponse
        """
        results = {}
        errors = {}

        for agent_type in self.AGENT_REGISTRY.keys():
            try:
                results[agent_type] = self.run_analysis(
                    agent_type=agent_type,
                    save_task=save_tasks
                )
            except AgentError as e:
                logger.warning(f"Agent {agent_type} failed: {e}")
                errors[agent_type] = str(e)

        if errors:
            logger.warning(f"Some agents failed: {errors}")

        return results

    def get_consolidated_recommendations(
        self,
        agent_types: List[str] = None,
        max_recommendations: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get consolidated recommendations from multiple agents.

        Args:
            agent_types: List of agents to query (all if None)
            max_recommendations: Maximum recommendations to return

        Returns:
            List of consolidated, prioritized recommendations
        """
        if agent_types is None:
            agent_types = list(self.AGENT_REGISTRY.keys())

        all_recommendations = []

        for agent_type in agent_types:
            try:
                agent = self.get_agent(agent_type)
                recommendations = agent.get_recommendations()

                # Add agent source
                for rec in recommendations:
                    rec['source_agent'] = agent_type

                all_recommendations.extend(recommendations)

            except Exception as e:
                logger.warning(f"Failed to get recommendations from {agent_type}: {e}")

        # Deduplicate and prioritize
        consolidated = self._consolidate_recommendations(all_recommendations)

        # Sort by priority
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        consolidated.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 4))

        return consolidated[:max_recommendations]

    def _consolidate_recommendations(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Consolidate and deduplicate recommendations.

        Args:
            recommendations: List of all recommendations

        Returns:
            Consolidated list
        """
        # Group by type
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for rec in recommendations:
            rec_type = rec.get('type', 'other')
            if rec_type not in by_type:
                by_type[rec_type] = []
            by_type[rec_type].append(rec)

        consolidated = []
        for rec_type, recs in by_type.items():
            if len(recs) == 1:
                consolidated.append(recs[0])
            else:
                # Merge similar recommendations
                merged = self._merge_recommendations(recs)
                consolidated.append(merged)

        return consolidated

    def _merge_recommendations(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge similar recommendations from different agents.

        Args:
            recommendations: List of similar recommendations

        Returns:
            Merged recommendation
        """
        if not recommendations:
            return {}

        # Use highest priority
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        highest_priority = min(recommendations, key=lambda x: priority_order.get(x.get('priority', 'low'), 4))

        # Combine sources
        sources = list(set(r.get('source_agent', '') for r in recommendations))

        # Combine details
        combined_details = {}
        for rec in recommendations:
            combined_details.update(rec.get('details', {}))

        return {
            'type': recommendations[0].get('type'),
            'priority': highest_priority.get('priority'),
            'description': highest_priority.get('description'),
            'details': combined_details,
            'expected_impact': highest_priority.get('expected_impact'),
            'source_agents': sources,
            'consensus_count': len(recommendations),
            'created_at': datetime.now(timezone.utc).isoformat()
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents.

        Returns:
            Dictionary with agent statuses
        """
        import uuid as uuid_module
        status = {
            'available_agents': list(self.AGENT_REGISTRY.keys()),
            'initialized_agents': list(self._agents.keys()),
            'user_id': self.user_id,
            'portfolio_loaded': bool(self.portfolio_data)
        }

        # Get recent tasks for this user
        if self.user_id:
            # Convert string user_id to UUID for query
            user_uuid = uuid_module.UUID(self.user_id) if isinstance(self.user_id, str) else self.user_id
            recent_tasks = AgentTask.query.filter_by(
                user_id=user_uuid
            ).order_by(AgentTask.created_at.desc()).limit(10).all()

            status['recent_tasks'] = [
                task.to_dict() for task in recent_tasks
            ]

        return status

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """
        Get a specific task by ID.

        Args:
            task_id: Task UUID

        Returns:
            AgentTask or None
        """
        import uuid as uuid_module
        try:
            task_uuid = uuid_module.UUID(task_id) if isinstance(task_id, str) else task_id
            return db.session.get(AgentTask, task_uuid)
        except (ValueError, TypeError):
            return None

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or processing task.

        Args:
            task_id: Task UUID

        Returns:
            True if cancelled successfully
        """
        task = self.get_task(task_id)
        if not task:
            return False

        if task.status in ['pending', 'processing']:
            task.cancel()
            db.session.commit()
            return True

        return False

    def retry_task(self, task_id: str) -> Optional[AgentResponse]:
        """
        Retry a failed task.

        Args:
            task_id: Task UUID

        Returns:
            AgentResponse if retry successful, None otherwise
        """
        task = self.get_task(task_id)
        if not task or not task.can_retry:
            return None

        if task.retry():
            db.session.commit()

            # Re-run the analysis
            return self.run_analysis(
                agent_type=task.agent_type,
                task_type=task.task_type,
                save_task=False  # Use existing task
            )

        return None

    @staticmethod
    def get_available_agents() -> List[Dict[str, str]]:
        """
        Get list of available agents and their descriptions.

        Returns:
            List of agent info dictionaries
        """
        return [
            {
                'type': 'cfa',
                'name': 'CFA Agent',
                'description': 'Investment analysis, portfolio metrics, and security recommendations'
            },
            {
                'type': 'cfp',
                'name': 'CFP Agent',
                'description': 'Financial planning, retirement analysis, and goal-based planning'
            },
            {
                'type': 'cio',
                'name': 'CIO Agent',
                'description': 'Strategic allocation, investment policy, and portfolio oversight'
            },
            {
                'type': 'accountant',
                'name': 'Accountant Agent',
                'description': 'Tax optimization, compliance, and financial record keeping'
            },
            {
                'type': 'quant_risk',
                'name': 'Quant Risk Agent',
                'description': 'Risk modeling, VaR analysis, and stress testing'
            },
            {
                'type': 'quant_strategy',
                'name': 'Quant Strategy Agent',
                'description': 'Quantitative strategies, factor analysis, and portfolio optimization'
            }
        ]
