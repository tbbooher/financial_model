"""
Family Office Platform - Base Agent

Provides the abstract base class for all AI agents with common functionality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging


@dataclass
class AgentResponse:
    """
    Standardized response structure for agent analysis.

    Attributes:
        agent_type: Type/name of the agent
        recommendations: List of actionable recommendations
        confidence_score: Confidence in the analysis (0.0 to 1.0)
        reasoning: Explanation of the analysis logic
        data_sources: List of data sources used
        timestamp: When the analysis was performed
        metadata: Additional metadata
    """
    agent_type: str
    recommendations: List[Dict[str, Any]]
    confidence_score: float
    reasoning: str
    data_sources: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'agent_type': self.agent_type,
            'recommendations': self.recommendations,
            'confidence_score': self.confidence_score,
            'reasoning': self.reasoning,
            'data_sources': self.data_sources,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class BaseAgent(ABC):
    """
    Abstract base class for all family office AI agents.

    All specialized agents must inherit from this class and implement
    the analyze() and get_recommendations() methods.
    """

    def __init__(self, user_id: str, portfolio_data: Dict[str, Any]):
        """
        Initialize base agent.

        Args:
            user_id: User ID for the analysis
            portfolio_data: Portfolio data dictionary
        """
        self.user_id = user_id
        self.portfolio_data = portfolio_data
        self.agent_type = self._get_agent_type()
        self.logger = logging.getLogger(f'agent.{self.agent_type}')
        self._analysis_cache = {}

    def _get_agent_type(self) -> str:
        """Get agent type from class name."""
        name = self.__class__.__name__.lower()
        # Remove 'agent' suffix if present
        if name.endswith('agent'):
            name = name[:-5]
        return name

    @abstractmethod
    def analyze(self) -> AgentResponse:
        """
        Perform agent-specific analysis.

        Must be implemented by all subclasses.

        Returns:
            AgentResponse with analysis results
        """
        pass

    @abstractmethod
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate specific recommendations.

        Must be implemented by all subclasses.

        Returns:
            List of recommendation dictionaries
        """
        pass

    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """
        Calculate confidence score based on multiple factors.

        Args:
            factors: Dictionary of factor names and scores (0-1)

        Returns:
            Overall confidence score (0-1)
        """
        if not factors:
            return 0.5

        # Weighted average of factors
        total = sum(factors.values())
        count = len(factors)

        if count == 0:
            return 0.5

        confidence = total / count

        # Ensure bounds
        return max(0.0, min(1.0, confidence))

    def _assess_data_quality(self) -> float:
        """
        Assess the quality of available data.

        Returns:
            Data quality score (0-1)
        """
        score = 0.0
        checks = 0

        # Check if portfolio data exists
        if self.portfolio_data:
            score += 0.2
        checks += 1

        # Check if assets exist
        assets = self.portfolio_data.get('assets', [])
        if assets:
            score += 0.2
            # Check for complete asset data
            complete_assets = sum(
                1 for a in assets
                if a.get('current_value') and a.get('symbol')
            )
            score += 0.2 * (complete_assets / len(assets)) if assets else 0
        checks += 2

        # Check for performance data
        if self.portfolio_data.get('performance'):
            score += 0.2
        checks += 1

        # Check for total value
        if self.portfolio_data.get('total_value', 0) > 0:
            score += 0.2
        checks += 1

        return min(1.0, score)

    def _assess_market_conditions(self) -> float:
        """
        Assess current market conditions for confidence adjustment.

        Returns:
            Market stability score (0-1)
        """
        # Default to moderate stability
        # In production, this would check VIX, market trends, etc.
        return 0.7

    def _log_analysis(self, analysis_type: str, result: Any):
        """
        Log analysis for audit trail.

        Args:
            analysis_type: Type of analysis performed
            result: Analysis result
        """
        self.logger.info(
            f"Analysis completed: {analysis_type} for user {self.user_id}"
        )

    def _create_recommendation(
        self,
        rec_type: str,
        priority: str,
        description: str,
        details: Dict[str, Any] = None,
        expected_impact: str = None
    ) -> Dict[str, Any]:
        """
        Create a standardized recommendation.

        Args:
            rec_type: Recommendation type
            priority: Priority level (low, medium, high, urgent)
            description: Brief description
            details: Additional details
            expected_impact: Expected outcome

        Returns:
            Recommendation dictionary
        """
        return {
            'type': rec_type,
            'priority': priority,
            'description': description,
            'details': details or {},
            'expected_impact': expected_impact,
            'agent': self.agent_type,
            'created_at': datetime.now(timezone.utc).isoformat()
        }

    def _get_portfolio_value(self) -> float:
        """Get total portfolio value."""
        return float(self.portfolio_data.get('total_value', 0) or
                    self.portfolio_data.get('net_worth', 0) or
                    self.portfolio_data.get('total_assets', 0))

    def _get_assets(self) -> List[Dict[str, Any]]:
        """Get list of assets."""
        return self.portfolio_data.get('assets', []) or \
               self.portfolio_data.get('holdings', [])

    def _get_risk_tolerance(self) -> str:
        """Get user's risk tolerance."""
        return self.portfolio_data.get('risk_tolerance', 'moderate')
