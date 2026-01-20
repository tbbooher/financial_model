"""
Family Office Platform - Agent Unit Tests

Tests for AI agent functionality.
"""

import pytest
from unittest.mock import Mock, patch

from app.agents.base_agent import BaseAgent, AgentResponse
from app.agents.cfa_agent import CFAAgent
from app.agents.cfp_agent import CFPAgent
from app.agents.cio_agent import CIOAgent
from app.agents.accountant_agent import AccountantAgent
from app.agents.quant_analyst import QuantAnalyst
from app.agents.agent_manager import AgentManager
from app.utils.exceptions import AgentError


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_create_agent_response(self):
        """Test creating an AgentResponse."""
        response = AgentResponse(
            agent_type='cfa',
            recommendations=[
                {'type': 'rebalance', 'priority': 'high', 'description': 'Test'}
            ],
            confidence_score=0.85,
            reasoning='Test reasoning',
            data_sources=['market_data'],
            timestamp='2024-01-01T00:00:00'
        )

        assert response.agent_type == 'cfa'
        assert len(response.recommendations) == 1
        assert response.confidence_score == 0.85

    def test_agent_response_to_dict(self):
        """Test AgentResponse serialization."""
        response = AgentResponse(
            agent_type='cfp',
            recommendations=[],
            confidence_score=0.75,
            reasoning='Test',
            data_sources=[],
            timestamp='2024-01-01T00:00:00'
        )

        result = response.to_dict()

        assert isinstance(result, dict)
        assert result['agent_type'] == 'cfp'
        assert result['confidence_score'] == 0.75


class TestCFAAgent:
    """Tests for the CFA Agent."""

    def test_analyze(self, app, sample_portfolio_data):
        """Test CFA agent analysis."""
        with app.app_context():
            agent = CFAAgent(
                user_id='test-user',
                portfolio_data=sample_portfolio_data
            )

            response = agent.analyze()

            assert isinstance(response, AgentResponse)
            assert response.agent_type == 'cfa'
            assert 0 <= response.confidence_score <= 1

    def test_get_recommendations(self, app, sample_portfolio_data):
        """Test CFA agent recommendations."""
        with app.app_context():
            agent = CFAAgent(
                user_id='test-user',
                portfolio_data=sample_portfolio_data
            )

            recommendations = agent.get_recommendations()

            assert isinstance(recommendations, list)
            for rec in recommendations:
                assert 'type' in rec
                assert 'priority' in rec
                assert 'description' in rec


class TestCFPAgent:
    """Tests for the CFP Agent."""

    def test_analyze(self, app, sample_portfolio_data):
        """Test CFP agent analysis."""
        with app.app_context():
            agent = CFPAgent(
                user_id='test-user',
                portfolio_data=sample_portfolio_data
            )

            response = agent.analyze()

            assert isinstance(response, AgentResponse)
            assert response.agent_type == 'cfp'

    def test_retirement_analysis(self, app, sample_portfolio_data):
        """Test retirement analysis."""
        with app.app_context():
            agent = CFPAgent(
                user_id='test-user',
                portfolio_data=sample_portfolio_data
            )

            retirement = agent._analyze_retirement_readiness()

            # Actual keys returned by the method
            assert 'current_retirement_assets' in retirement
            assert 'projected_value_at_retirement' in retirement


class TestCIOAgent:
    """Tests for the CIO Agent."""

    def test_analyze(self, app, sample_portfolio_data):
        """Test CIO agent analysis."""
        with app.app_context():
            agent = CIOAgent(
                user_id='test-user',
                portfolio_data=sample_portfolio_data
            )

            response = agent.analyze()

            assert isinstance(response, AgentResponse)
            assert response.agent_type == 'cio'

    def test_strategic_allocation(self, app, sample_portfolio_data):
        """Test strategic allocation analysis."""
        with app.app_context():
            agent = CIOAgent(
                user_id='test-user',
                portfolio_data=sample_portfolio_data
            )

            allocation = agent._strategic_asset_allocation()

            assert 'current_allocation' in allocation
            assert 'strategic_allocation' in allocation


class TestAccountantAgent:
    """Tests for the Accountant Agent."""

    def test_analyze(self, app, sample_portfolio_data):
        """Test accountant agent analysis."""
        with app.app_context():
            agent = AccountantAgent(
                user_id='test-user',
                portfolio_data=sample_portfolio_data
            )

            response = agent.analyze()

            assert isinstance(response, AgentResponse)
            assert response.agent_type == 'accountant'

    def test_tax_loss_harvesting(self, app, sample_portfolio_data):
        """Test tax loss harvesting analysis."""
        with app.app_context():
            agent = AccountantAgent(
                user_id='test-user',
                portfolio_data=sample_portfolio_data
            )

            tlh = agent._analyze_tax_loss_harvesting()

            # Actual keys returned by the method
            assert 'candidates' in tlh
            assert 'harvesting_recommended' in tlh


class TestQuantAnalyst:
    """Tests for the Quant Analyst Agent."""

    def test_analyze_risk_specialty(self, app, sample_portfolio_data):
        """Test quant analyst with risk modeling specialty."""
        with app.app_context():
            agent = QuantAnalyst(
                user_id='test-user',
                portfolio_data=sample_portfolio_data,
                specialty='risk_modeling'
            )

            response = agent.analyze()

            assert isinstance(response, AgentResponse)
            # Actual agent_type is 'quantanalyst_risk'
            assert 'risk' in response.agent_type

    def test_analyze_strategy_specialty(self, app, sample_portfolio_data):
        """Test quant analyst with strategy development specialty."""
        with app.app_context():
            agent = QuantAnalyst(
                user_id='test-user',
                portfolio_data=sample_portfolio_data,
                specialty='strategy_development'
            )

            response = agent.analyze()

            assert isinstance(response, AgentResponse)
            # Actual agent_type is 'quantanalyst_strategy'
            assert 'strategy' in response.agent_type


class TestAgentManager:
    """Tests for the Agent Manager."""

    def test_get_available_agents(self, app):
        """Test getting available agents list."""
        with app.app_context():
            agents = AgentManager.get_available_agents()

            assert isinstance(agents, list)
            assert len(agents) > 0

            # The method returns 'type' key, not 'agent_type'
            agent_types = [a['type'] for a in agents]
            assert 'cfa' in agent_types
            assert 'cfp' in agent_types
            assert 'cio' in agent_types

    def test_run_analysis(self, app, sample_user, sample_portfolio_data, db_session):
        """Test running analysis with specific agent."""
        with app.app_context():
            manager = AgentManager(
                user_id=str(sample_user.id),
                portfolio_data=sample_portfolio_data
            )

            response = manager.run_analysis(
                agent_type='cfa',
                task_type='full_analysis',
                save_task=False
            )

            assert isinstance(response, AgentResponse)
            assert response.agent_type == 'cfa'

    def test_run_all_analyses(self, app, sample_user, sample_portfolio_data, db_session):
        """Test running all agents."""
        with app.app_context():
            manager = AgentManager(
                user_id=str(sample_user.id),
                portfolio_data=sample_portfolio_data
            )

            results = manager.run_all_analyses(save_tasks=False)

            assert isinstance(results, dict)
            assert len(results) > 0
            assert 'cfa' in results
            assert 'cfp' in results

    def test_get_consolidated_recommendations(self, app, sample_user, sample_portfolio_data, db_session):
        """Test getting consolidated recommendations."""
        with app.app_context():
            manager = AgentManager(
                user_id=str(sample_user.id),
                portfolio_data=sample_portfolio_data
            )

            # First run analyses
            manager.run_all_analyses(save_tasks=False)

            # Then get recommendations
            recommendations = manager.get_consolidated_recommendations(
                max_recommendations=10
            )

            assert isinstance(recommendations, list)

    def test_invalid_agent_type(self, app, sample_user, sample_portfolio_data):
        """Test running analysis with invalid agent type."""
        with app.app_context():
            manager = AgentManager(
                user_id=str(sample_user.id),
                portfolio_data=sample_portfolio_data
            )

            with pytest.raises(AgentError):
                manager.run_analysis(
                    agent_type='invalid_agent',
                    task_type='full_analysis',
                    save_task=False  # Skip database to test validation
                )
