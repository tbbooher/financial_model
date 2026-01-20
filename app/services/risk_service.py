"""
Family Office Platform - Risk Service

Provides risk management calculations including VaR, CVaR, Monte Carlo simulation,
stress testing, and correlation analysis.
"""

import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Tuple, Optional

from flask import current_app

from app.utils.exceptions import CalculationError


class RiskService:
    """
    Service for portfolio risk management and analysis.

    Provides:
    - Value at Risk (VaR) calculations
    - Conditional Value at Risk (CVaR/Expected Shortfall)
    - Monte Carlo simulations
    - Stress testing
    - Correlation analysis
    - Risk-adjusted performance metrics
    """

    def __init__(self, portfolio_data: Dict[str, Any] = None):
        """
        Initialize risk service.

        Args:
            portfolio_data: Portfolio data for analysis
        """
        self.portfolio_data = portfolio_data or {}
        self._returns_cache = None

    def calculate_var(
        self,
        confidence_level: float = 0.95,
        time_horizon: int = 1,
        method: str = 'historical'
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR).

        VaR represents the maximum expected loss at a given confidence level
        over a specified time horizon.

        Args:
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            time_horizon: Time horizon in days
            method: Calculation method ('historical', 'parametric', 'monte_carlo')

        Returns:
            Dictionary with VaR results
        """
        portfolio_value = self.portfolio_data.get('total_value', 0)
        if portfolio_value == 0:
            return {
                'var_absolute': 0.0,
                'var_percentage': 0.0,
                'confidence_level': confidence_level,
                'time_horizon_days': time_horizon,
                'method': method
            }

        returns = self._get_portfolio_returns()

        if method == 'historical':
            var_pct = self._historical_var(returns, confidence_level, time_horizon)
        elif method == 'parametric':
            var_pct = self._parametric_var(returns, confidence_level, time_horizon)
        elif method == 'monte_carlo':
            var_pct = self._monte_carlo_var(returns, confidence_level, time_horizon)
        else:
            raise CalculationError(f"Unknown VaR method: {method}", calculation_type='var')

        var_absolute = float(portfolio_value) * abs(var_pct)

        return {
            'var_absolute': round(var_absolute, 2),
            'var_percentage': round(var_pct * 100, 4),
            'confidence_level': confidence_level,
            'time_horizon_days': time_horizon,
            'method': method,
            'portfolio_value': float(portfolio_value)
        }

    def _historical_var(
        self,
        returns: np.ndarray,
        confidence_level: float,
        time_horizon: int
    ) -> float:
        """Calculate VaR using historical simulation method."""
        if len(returns) == 0:
            return 0.0

        # Scale returns for time horizon
        scaled_returns = returns * np.sqrt(time_horizon)

        # Calculate VaR as percentile
        var = np.percentile(scaled_returns, (1 - confidence_level) * 100)

        return float(var)

    def _parametric_var(
        self,
        returns: np.ndarray,
        confidence_level: float,
        time_horizon: int
    ) -> float:
        """Calculate VaR using parametric (variance-covariance) method."""
        if len(returns) == 0:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)

        # VaR formula: μ - z * σ * √t
        var = mean_return * time_horizon - z_score * std_return * np.sqrt(time_horizon)

        return float(var)

    def _monte_carlo_var(
        self,
        returns: np.ndarray,
        confidence_level: float,
        time_horizon: int,
        simulations: int = 10000
    ) -> float:
        """Calculate VaR using Monte Carlo simulation."""
        if len(returns) == 0:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Generate random scenarios
        simulated_returns = np.random.normal(
            mean_return * time_horizon,
            std_return * np.sqrt(time_horizon),
            simulations
        )

        # Calculate VaR as percentile of simulated returns
        var = np.percentile(simulated_returns, (1 - confidence_level) * 100)

        return float(var)

    def calculate_cvar(
        self,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> Dict[str, float]:
        """
        Calculate Conditional Value at Risk (CVaR/Expected Shortfall).

        CVaR is the expected loss given that the loss exceeds VaR.

        Args:
            confidence_level: Confidence level
            time_horizon: Time horizon in days

        Returns:
            Dictionary with CVaR results
        """
        portfolio_value = self.portfolio_data.get('total_value', 0)
        returns = self._get_portfolio_returns()

        if len(returns) == 0 or portfolio_value == 0:
            return {
                'cvar_absolute': 0.0,
                'cvar_percentage': 0.0,
                'confidence_level': confidence_level,
                'time_horizon_days': time_horizon
            }

        # Scale returns for time horizon
        scaled_returns = returns * np.sqrt(time_horizon)

        # Get VaR threshold
        var_threshold = np.percentile(scaled_returns, (1 - confidence_level) * 100)

        # CVaR is mean of returns below VaR threshold
        tail_returns = scaled_returns[scaled_returns <= var_threshold]

        if len(tail_returns) == 0:
            cvar_pct = var_threshold
        else:
            cvar_pct = np.mean(tail_returns)

        cvar_absolute = float(portfolio_value) * abs(cvar_pct)

        return {
            'cvar_absolute': round(cvar_absolute, 2),
            'cvar_percentage': round(cvar_pct * 100, 4),
            'confidence_level': confidence_level,
            'time_horizon_days': time_horizon,
            'var_percentage': round(var_threshold * 100, 4)
        }

    def monte_carlo_simulation(
        self,
        time_horizon_years: float = 1.0,
        simulations: int = 10000
    ) -> Dict[str, Any]:
        """
        Perform Monte Carlo simulation for portfolio outcomes.

        Args:
            time_horizon_years: Projection period in years
            simulations: Number of scenarios to simulate

        Returns:
            Dictionary with simulation results
        """
        portfolio_value = float(self.portfolio_data.get('total_value', 0))
        if portfolio_value == 0:
            return {'error': 'Portfolio value is zero'}

        returns = self._get_portfolio_returns()
        if len(returns) == 0:
            # Use default parameters if no return data
            mean_return = 0.08  # 8% annual
            std_return = 0.15   # 15% volatility
        else:
            # Annualize returns
            mean_return = np.mean(returns) * 252
            std_return = np.std(returns) * np.sqrt(252)

        # Generate simulated end values
        random_returns = np.random.normal(
            mean_return * time_horizon_years,
            std_return * np.sqrt(time_horizon_years),
            simulations
        )

        end_values = portfolio_value * (1 + random_returns)

        # Calculate statistics
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        percentile_values = {
            f'p{p}': round(np.percentile(end_values, p), 2)
            for p in percentiles
        }

        return {
            'initial_value': portfolio_value,
            'time_horizon_years': time_horizon_years,
            'simulations': simulations,
            'expected_return': round(mean_return, 4),
            'volatility': round(std_return, 4),
            'mean_end_value': round(np.mean(end_values), 2),
            'median_end_value': round(np.median(end_values), 2),
            'std_end_value': round(np.std(end_values), 2),
            'min_end_value': round(np.min(end_values), 2),
            'max_end_value': round(np.max(end_values), 2),
            'percentiles': percentile_values,
            'probability_of_loss': round(np.mean(end_values < portfolio_value) * 100, 2),
            'probability_of_gain': round(np.mean(end_values > portfolio_value) * 100, 2)
        }

    def stress_test(
        self,
        scenarios: Dict[str, Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Perform stress testing on portfolio.

        Args:
            scenarios: Dictionary of stress scenarios with factor changes

        Returns:
            Dictionary with stress test results
        """
        portfolio_value = float(self.portfolio_data.get('total_value', 0))

        if scenarios is None:
            # Default stress scenarios
            scenarios = {
                '2008_financial_crisis': {'equity': -0.50, 'bonds': 0.05, 'real_estate': -0.30},
                'covid_march_2020': {'equity': -0.35, 'bonds': 0.03, 'real_estate': -0.10},
                'dot_com_crash': {'equity': -0.45, 'bonds': 0.10, 'real_estate': 0.05},
                'interest_rate_shock_up': {'equity': -0.15, 'bonds': -0.10, 'real_estate': -0.05},
                'interest_rate_shock_down': {'equity': 0.10, 'bonds': 0.15, 'real_estate': 0.05},
                'inflation_spike': {'equity': -0.10, 'bonds': -0.15, 'real_estate': 0.10},
                'recession': {'equity': -0.30, 'bonds': 0.08, 'real_estate': -0.20}
            }

        # Get current allocation
        allocation = self._get_allocation_weights()

        results = {}
        for scenario_name, factor_changes in scenarios.items():
            # Calculate portfolio impact
            impact = 0.0

            for asset_class, weight in allocation.items():
                # Map asset types to scenario factors
                if asset_class in ['stock', 'etf', 'mutual_fund', 'investments']:
                    factor = factor_changes.get('equity', 0)
                elif asset_class in ['bond']:
                    factor = factor_changes.get('bonds', 0)
                elif asset_class == 'real_estate':
                    factor = factor_changes.get('real_estate', 0)
                else:
                    factor = 0

                impact += weight * factor

            stressed_value = portfolio_value * (1 + impact)
            loss = portfolio_value - stressed_value

            results[scenario_name] = {
                'impact_percentage': round(impact * 100, 2),
                'stressed_value': round(stressed_value, 2),
                'loss': round(loss, 2),
                'factor_changes': factor_changes
            }

        return {
            'portfolio_value': portfolio_value,
            'scenarios': results,
            'worst_case': min(results.items(), key=lambda x: x[1]['stressed_value'])[0]
        }

    def correlation_analysis(self) -> Dict[str, Any]:
        """
        Analyze correlations between portfolio assets.

        Returns:
            Dictionary with correlation matrix and analysis
        """
        assets = self.portfolio_data.get('assets', [])

        if len(assets) < 2:
            return {'error': 'Need at least 2 assets for correlation analysis'}

        try:
            import yfinance as yf

            # Get symbols
            symbols = [
                asset['symbol'] for asset in assets
                if asset.get('symbol') and asset.get('asset_type') in ['stock', 'etf', 'mutual_fund']
            ]

            if len(symbols) < 2:
                return {'error': 'Need at least 2 tradeable assets with symbols'}

            # Download price data
            data = yf.download(symbols, period='1y', progress=False)['Adj Close']

            if data.empty:
                return {'error': 'Could not retrieve price data'}

            # Calculate returns
            returns = data.pct_change().dropna()

            # Calculate correlation matrix
            correlation_matrix = returns.corr()

            # Convert to serializable format
            corr_dict = {
                'symbols': symbols,
                'matrix': correlation_matrix.values.tolist(),
                'pairs': []
            }

            # Extract significant correlations
            for i, sym1 in enumerate(symbols):
                for j, sym2 in enumerate(symbols):
                    if i < j:
                        corr = correlation_matrix.iloc[i, j]
                        corr_dict['pairs'].append({
                            'asset1': sym1,
                            'asset2': sym2,
                            'correlation': round(corr, 4),
                            'strength': self._classify_correlation(corr)
                        })

            # Calculate average correlation
            upper_triangle = correlation_matrix.values[np.triu_indices(len(symbols), k=1)]
            avg_correlation = np.mean(upper_triangle)

            corr_dict['average_correlation'] = round(avg_correlation, 4)
            corr_dict['diversification_score'] = round(1 - abs(avg_correlation), 4)

            return corr_dict

        except Exception as e:
            return {'error': f'Correlation analysis failed: {str(e)}'}

    def calculate_sharpe_ratio(
        self,
        returns: np.ndarray = None,
        risk_free_rate: float = None
    ) -> float:
        """
        Calculate Sharpe Ratio.

        Sharpe = (Rp - Rf) / σp

        Args:
            returns: Portfolio returns (uses cached if not provided)
            risk_free_rate: Risk-free rate

        Returns:
            Sharpe ratio
        """
        if returns is None:
            returns = self._get_portfolio_returns()

        if len(returns) == 0:
            return 0.0

        if risk_free_rate is None:
            risk_free_rate = float(current_app.config.get('DEFAULT_RISK_FREE_RATE', 0.02))

        # Annualize returns
        annual_return = np.mean(returns) * 252
        annual_volatility = np.std(returns) * np.sqrt(252)

        if annual_volatility == 0:
            return 0.0

        sharpe = (annual_return - risk_free_rate) / annual_volatility

        return round(float(sharpe), 4)

    def calculate_treynor_ratio(
        self,
        returns: np.ndarray = None,
        beta: float = 1.0,
        risk_free_rate: float = None
    ) -> float:
        """
        Calculate Treynor Ratio.

        Treynor = (Rp - Rf) / βp

        Args:
            returns: Portfolio returns
            beta: Portfolio beta
            risk_free_rate: Risk-free rate

        Returns:
            Treynor ratio
        """
        if returns is None:
            returns = self._get_portfolio_returns()

        if len(returns) == 0 or beta == 0:
            return 0.0

        if risk_free_rate is None:
            risk_free_rate = float(current_app.config.get('DEFAULT_RISK_FREE_RATE', 0.02))

        annual_return = np.mean(returns) * 252

        treynor = (annual_return - risk_free_rate) / beta

        return round(float(treynor), 4)

    def calculate_max_drawdown(self, returns: np.ndarray = None) -> Dict[str, float]:
        """
        Calculate Maximum Drawdown.

        Args:
            returns: Portfolio returns

        Returns:
            Dictionary with max drawdown metrics
        """
        if returns is None:
            returns = self._get_portfolio_returns()

        if len(returns) == 0:
            return {'max_drawdown': 0.0, 'max_drawdown_duration': 0}

        # Calculate cumulative returns
        cumulative = (1 + returns).cumprod()

        # Calculate running maximum
        running_max = np.maximum.accumulate(cumulative)

        # Calculate drawdowns
        drawdowns = (cumulative - running_max) / running_max

        max_drawdown = np.min(drawdowns)

        return {
            'max_drawdown': round(float(max_drawdown) * 100, 4),
            'current_drawdown': round(float(drawdowns[-1]) * 100, 4) if len(drawdowns) > 0 else 0.0
        }

    def _get_portfolio_returns(self) -> np.ndarray:
        """Get portfolio returns from cache or calculate."""
        if self._returns_cache is not None:
            return self._returns_cache

        # Try to get actual returns from assets
        assets = self.portfolio_data.get('assets', [])

        if not assets:
            # Return empty array if no assets
            return np.array([])

        try:
            import yfinance as yf

            symbols = [
                asset['symbol'] for asset in assets
                if asset.get('symbol') and asset.get('asset_type') in ['stock', 'etf', 'mutual_fund']
            ]

            if not symbols:
                return np.array([])

            # Download price data
            data = yf.download(symbols, period='1y', progress=False)['Adj Close']

            if data.empty:
                return np.array([])

            # Calculate weighted portfolio returns
            returns = data.pct_change().dropna()

            # Weight by value
            total_value = sum(
                asset.get('current_value', 0) for asset in assets
                if asset.get('symbol') in symbols
            )

            if total_value == 0:
                return returns.mean(axis=1).values

            weights = []
            for symbol in returns.columns:
                asset_value = next(
                    (a['current_value'] for a in assets if a.get('symbol') == symbol),
                    0
                )
                weights.append(asset_value / total_value if total_value > 0 else 0)

            portfolio_returns = (returns * weights).sum(axis=1)

            self._returns_cache = portfolio_returns.values
            return self._returns_cache

        except:
            return np.array([])

    def _get_allocation_weights(self) -> Dict[str, float]:
        """Get current allocation weights."""
        breakdown = self.portfolio_data.get('breakdown', {})
        total = sum(breakdown.values()) if breakdown else 0

        if total == 0:
            return {}

        return {
            asset_type: value / total
            for asset_type, value in breakdown.items()
        }

    def _classify_correlation(self, corr: float) -> str:
        """Classify correlation strength."""
        abs_corr = abs(corr)
        if abs_corr >= 0.8:
            return 'very_strong'
        elif abs_corr >= 0.6:
            return 'strong'
        elif abs_corr >= 0.4:
            return 'moderate'
        elif abs_corr >= 0.2:
            return 'weak'
        else:
            return 'very_weak'
