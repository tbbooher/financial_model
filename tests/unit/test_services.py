"""
Family Office Platform - Service Unit Tests

Tests for business logic services.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from app.services.portfolio_service import PortfolioService
from app.services.capm_service import CAPMService
from app.services.risk_service import RiskService
from app.services.auth_service import AuthService
from app.utils.exceptions import ValidationError, CalculationError, AuthenticationError


class TestAuthService:
    """Tests for the AuthService."""

    def test_create_user_success(self, app, db_session):
        """Test successful user creation."""
        with app.app_context():
            auth_service = AuthService()
            user = auth_service.create_user(
                email='newuser@test.com',
                password='ValidPassword123!',
                first_name='Test',
                last_name='User'
            )

            assert user is not None
            assert user.email == 'newuser@test.com'
            assert user.first_name == 'Test'

    def test_create_user_invalid_email(self, app, db_session):
        """Test user creation with invalid email."""
        with app.app_context():
            auth_service = AuthService()

            with pytest.raises(ValidationError):
                auth_service.create_user(
                    email='invalid-email',
                    password='ValidPassword123!'
                )

    def test_create_user_weak_password(self, app, db_session):
        """Test user creation with weak password."""
        with app.app_context():
            auth_service = AuthService()

            with pytest.raises(ValidationError):
                auth_service.create_user(
                    email='user@test.com',
                    password='weak'
                )

    def test_authenticate_success(self, app, sample_user):
        """Test successful authentication."""
        with app.app_context():
            auth_service = AuthService()
            user, tokens = auth_service.authenticate(
                email='test@example.com',
                password='TestPassword123!'
            )

            assert user is not None
            assert 'access_token' in tokens
            assert 'refresh_token' in tokens

    def test_authenticate_wrong_password(self, app, sample_user):
        """Test authentication with wrong password."""
        with app.app_context():
            auth_service = AuthService()

            with pytest.raises(AuthenticationError):
                auth_service.authenticate(
                    email='test@example.com',
                    password='WrongPassword123!'
                )


class TestCAPMService:
    """Tests for the CAPMService."""

    def test_calculate_expected_return(self, app):
        """Test CAPM expected return calculation."""
        with app.app_context():
            capm = CAPMService(risk_free_rate=0.02)

            # Beta = 1 should give market return
            expected = capm.calculate_expected_return(beta=1.0, market_return=0.08)
            assert expected == pytest.approx(0.08, rel=0.01)

            # Beta = 0 should give risk-free rate
            expected = capm.calculate_expected_return(beta=0.0, market_return=0.08)
            assert expected == pytest.approx(0.02, rel=0.01)

            # Beta > 1 should give higher than market return
            expected = capm.calculate_expected_return(beta=1.5, market_return=0.08)
            assert expected > 0.08

    def test_expected_return_formula(self, app):
        """Test CAPM formula: E(R) = Rf + β(Rm - Rf)."""
        with app.app_context():
            capm = CAPMService(risk_free_rate=0.03)

            beta = 1.2
            market_return = 0.10
            rf = 0.03

            # Manual calculation
            expected_manual = rf + beta * (market_return - rf)

            # Service calculation
            expected_service = capm.calculate_expected_return(beta, market_return)

            assert expected_service == pytest.approx(expected_manual, rel=0.001)

    def test_generate_security_market_line(self, app):
        """Test SML generation."""
        with app.app_context():
            capm = CAPMService(risk_free_rate=0.02)

            sml = capm.generate_security_market_line(beta_range=(0, 2), points=10)

            assert 'betas' in sml
            assert 'expected_returns' in sml
            assert len(sml['betas']) == 10
            assert len(sml['expected_returns']) == 10

            # First point (beta=0) should equal risk-free rate
            assert sml['expected_returns'][0] == pytest.approx(0.02, rel=0.01)

    @patch('yfinance.download')
    def test_calculate_beta(self, mock_download, app):
        """Test beta calculation."""
        with app.app_context():
            # Mock market and asset data
            import pandas as pd
            dates = pd.date_range('2022-01-01', periods=252)

            mock_asset_data = pd.Series(
                np.random.randn(252).cumsum() + 100,
                index=dates,
                name='Adj Close'
            )
            mock_market_data = pd.Series(
                np.random.randn(252).cumsum() + 100,
                index=dates,
                name='Adj Close'
            )

            mock_download.side_effect = [
                pd.DataFrame({'Adj Close': mock_asset_data}),
                pd.DataFrame({'Adj Close': mock_market_data})
            ]

            capm = CAPMService()
            beta = capm.calculate_beta('TEST', period='1y')

            # Beta should be a reasonable value
            assert -3 < beta < 3


class TestRiskService:
    """Tests for the RiskService."""

    def test_calculate_var(self, sample_portfolio_data):
        """Test VaR calculation."""
        risk_service = RiskService(sample_portfolio_data)

        var_result = risk_service.calculate_var(confidence_level=0.95, time_horizon=1)

        assert 'var_percentage' in var_result
        assert 'var_absolute' in var_result
        assert var_result['confidence_level'] == 0.95
        assert var_result['time_horizon_days'] == 1

    def test_calculate_cvar(self, sample_portfolio_data):
        """Test CVaR (Expected Shortfall) calculation."""
        risk_service = RiskService(sample_portfolio_data)

        cvar_result = risk_service.calculate_cvar(confidence_level=0.95, time_horizon=1)

        assert 'cvar_percentage' in cvar_result
        assert 'cvar_absolute' in cvar_result
        assert cvar_result['confidence_level'] == 0.95
        assert cvar_result['time_horizon_days'] == 1

    def test_calculate_sharpe_ratio(self, sample_portfolio_data):
        """Test Sharpe ratio calculation."""
        risk_service = RiskService(sample_portfolio_data)

        sharpe = risk_service.calculate_sharpe_ratio()

        # Sharpe ratio should be a reasonable value
        assert -5 < sharpe < 5

    def test_monte_carlo_simulation(self, sample_portfolio_data):
        """Test Monte Carlo simulation."""
        risk_service = RiskService(sample_portfolio_data)

        results = risk_service.monte_carlo_simulation(
            time_horizon_years=1,
            simulations=1000  # Reduced for faster testing
        )

        assert 'percentiles' in results
        assert 'mean_end_value' in results
        assert 'median_end_value' in results
        # Check percentile keys (format is 'p5', 'p50', 'p95', etc.)
        assert 'p5' in results['percentiles']
        assert 'p50' in results['percentiles']
        assert 'p95' in results['percentiles']

        # 5th percentile should be less than 95th
        assert results['percentiles']['p5'] < results['percentiles']['p95']

    def test_stress_test(self, sample_portfolio_data):
        """Test stress testing scenarios."""
        risk_service = RiskService(sample_portfolio_data)

        stress_results = risk_service.stress_test()

        assert 'scenarios' in stress_results
        assert 'portfolio_value' in stress_results
        assert len(stress_results['scenarios']) > 0

        # Check each scenario has required fields (scenarios is a dict)
        for scenario_name, scenario_data in stress_results['scenarios'].items():
            assert 'impact_percentage' in scenario_data
            assert 'stressed_value' in scenario_data
            assert 'loss' in scenario_data


class TestPortfolioService:
    """Tests for the PortfolioService."""

    def test_get_portfolio_summary(self, app, sample_user, sample_assets, sample_real_estate):
        """Test portfolio summary calculation."""
        with app.app_context():
            portfolio_service = PortfolioService(str(sample_user.id))

            summary = portfolio_service.get_portfolio_summary()

            assert 'net_worth' in summary
            assert 'total_assets' in summary
            assert 'breakdown' in summary
            assert summary['total_assets'] > 0

    def test_get_holdings(self, app, sample_user, sample_assets):
        """Test getting asset holdings."""
        with app.app_context():
            portfolio_service = PortfolioService(str(sample_user.id))

            holdings = portfolio_service.get_holdings()

            assert len(holdings) == len(sample_assets)
            for holding in holdings:
                assert 'symbol' in holding
                assert 'current_value' in holding

    def test_calculate_rebalancing_plan(self, app, sample_user, sample_assets):
        """Test rebalancing plan calculation."""
        with app.app_context():
            portfolio_service = PortfolioService(str(sample_user.id))

            # Set custom target allocation
            target_allocation = {
                'stocks': 0.60,
                'bonds': 0.30,
                'cash': 0.10
            }

            # Pass target_allocation as keyword argument
            plan = portfolio_service.calculate_rebalancing_plan(target_allocation=target_allocation)

            assert 'current_allocation' in plan
            assert 'target_allocation' in plan
            assert 'recommended_trades' in plan
