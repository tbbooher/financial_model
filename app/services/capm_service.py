"""
Family Office Platform - CAPM Service

Provides Capital Asset Pricing Model analysis, beta calculations,
expected returns, and security market line generation.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Tuple, Optional

from flask import current_app

from app.utils.exceptions import CalculationError, DataIntegrationError


class CAPMService:
    """
    Service for Capital Asset Pricing Model (CAPM) analysis.

    CAPM Formula: E(R) = Rf + β(Rm - Rf)

    Where:
        E(R) = Expected return of the asset
        Rf = Risk-free rate
        β = Beta of the asset
        Rm = Expected return of the market
    """

    def __init__(self, risk_free_rate: float = None, market_symbol: str = None):
        """
        Initialize CAPM service.

        Args:
            risk_free_rate: Risk-free rate (default from config)
            market_symbol: Market index symbol (default ^GSPC)
        """
        self.risk_free_rate = risk_free_rate or float(
            current_app.config.get('DEFAULT_RISK_FREE_RATE', 0.02)
        )
        self.market_symbol = market_symbol or current_app.config.get(
            'DEFAULT_MARKET_SYMBOL', '^GSPC'
        )
        self._market_data_cache = {}

    def calculate_beta(self, asset_symbol: str, period: str = '2y') -> float:
        """
        Calculate beta coefficient for an asset.

        Beta = Cov(Ra, Rm) / Var(Rm)

        Args:
            asset_symbol: Stock/ETF symbol
            period: Historical period for calculation

        Returns:
            Beta coefficient

        Raises:
            CalculationError: If calculation fails
        """
        try:
            import yfinance as yf

            # Get asset and market data
            asset_data = yf.download(asset_symbol, period=period, progress=False)
            market_data = yf.download(self.market_symbol, period=period, progress=False)

            if asset_data.empty or market_data.empty:
                raise CalculationError(
                    f"Insufficient data for beta calculation: {asset_symbol}",
                    calculation_type='beta'
                )

            # Calculate returns
            asset_returns = asset_data['Adj Close'].pct_change().dropna()
            market_returns = market_data['Adj Close'].pct_change().dropna()

            # Align data
            aligned_data = pd.concat([asset_returns, market_returns], axis=1).dropna()
            aligned_data.columns = ['asset', 'market']

            if len(aligned_data) < 50:
                raise CalculationError(
                    f"Insufficient data points for beta calculation: {len(aligned_data)} (need 50+)",
                    calculation_type='beta'
                )

            # Calculate beta using covariance method
            covariance = np.cov(aligned_data['asset'], aligned_data['market'])[0][1]
            market_variance = np.var(aligned_data['market'])

            if market_variance == 0:
                raise CalculationError(
                    "Market variance is zero, cannot calculate beta",
                    calculation_type='beta'
                )

            beta = covariance / market_variance

            return round(float(beta), 6)

        except ImportError:
            # Fallback if yfinance not available - return market beta
            return 1.0
        except Exception as e:
            if isinstance(e, CalculationError):
                raise
            raise CalculationError(
                f"Beta calculation failed for {asset_symbol}: {str(e)}",
                calculation_type='beta'
            )

    def calculate_expected_return(self, beta: float, market_return: float = None) -> float:
        """
        Calculate expected return using CAPM formula.

        E(R) = Rf + β(Rm - Rf)

        Args:
            beta: Asset beta
            market_return: Expected market return (defaults to historical average)

        Returns:
            Expected return as decimal (e.g., 0.12 for 12%)
        """
        if market_return is None:
            market_return = self._get_market_expected_return()

        expected_return = self.risk_free_rate + beta * (market_return - self.risk_free_rate)

        return round(float(expected_return), 6)

    def calculate_portfolio_beta(self, portfolio_data: Dict[str, Any]) -> float:
        """
        Calculate weighted portfolio beta.

        Portfolio Beta = Σ(wi × βi)

        Args:
            portfolio_data: Portfolio data with assets and values

        Returns:
            Portfolio beta
        """
        total_value = Decimal(str(portfolio_data.get('total_value', 0)))
        if total_value == 0:
            return 1.0  # Default to market beta

        weighted_beta = Decimal('0.0')
        assets = portfolio_data.get('assets', [])

        for asset in assets:
            asset_type = asset.get('asset_type', '')

            # Only calculate beta for tradeable securities
            if asset_type not in ['stock', 'etf', 'mutual_fund']:
                continue

            asset_value = Decimal(str(asset.get('current_value', 0)))
            if asset_value <= 0:
                continue

            weight = asset_value / total_value

            # Get beta (use cached if available)
            symbol = asset.get('symbol', '')
            if symbol:
                try:
                    asset_beta = Decimal(str(asset.get('beta') or self.calculate_beta(symbol)))
                except:
                    asset_beta = Decimal('1.0')  # Default to market beta
            else:
                asset_beta = Decimal('1.0')

            weighted_beta += weight * asset_beta

        return round(float(weighted_beta), 6)

    def generate_security_market_line(
        self,
        beta_range: Tuple[float, float] = (0.0, 2.0),
        points: int = 100
    ) -> Dict[str, List[float]]:
        """
        Generate Security Market Line (SML) data points.

        SML: E(R) = Rf + β(Rm - Rf)

        Args:
            beta_range: Range of beta values (min, max)
            points: Number of data points

        Returns:
            Dictionary with betas and expected returns for plotting
        """
        market_return = self._get_market_expected_return()

        betas = np.linspace(beta_range[0], beta_range[1], points)
        expected_returns = [
            self.calculate_expected_return(beta, market_return)
            for beta in betas
        ]

        return {
            'betas': betas.tolist(),
            'expected_returns': expected_returns,
            'risk_free_rate': self.risk_free_rate,
            'market_return': market_return,
            'market_point': {
                'beta': 1.0,
                'return': market_return
            }
        }

    def analyze_asset_pricing(self, portfolio_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze if assets are fairly priced according to CAPM.

        Args:
            portfolio_data: Portfolio data with assets

        Returns:
            List of asset analysis results
        """
        analysis_results = []
        market_return = self._get_market_expected_return()

        assets = portfolio_data.get('assets', [])

        for asset in assets:
            asset_type = asset.get('asset_type', '')

            # Only analyze tradeable securities
            if asset_type not in ['stock', 'etf', 'mutual_fund']:
                continue

            symbol = asset.get('symbol', '')
            if not symbol:
                continue

            try:
                # Get beta
                beta = asset.get('beta')
                if beta is None:
                    beta = self.calculate_beta(symbol)

                # Calculate expected return from CAPM
                expected_return = self.calculate_expected_return(beta, market_return)

                # Get actual return (1Y if available)
                actual_return = asset.get('return_1y', 0) or 0

                # Calculate alpha (Jensen's Alpha)
                alpha = actual_return - expected_return

                # Determine valuation
                valuation = self._determine_valuation(alpha)
                recommendation = self._generate_recommendation(alpha, beta)

                analysis_results.append({
                    'symbol': symbol,
                    'name': asset.get('name', symbol),
                    'asset_type': asset_type,
                    'current_value': asset.get('current_value', 0),
                    'beta': round(beta, 4),
                    'expected_return': round(expected_return, 4),
                    'actual_return': round(actual_return, 4),
                    'alpha': round(alpha, 4),
                    'valuation': valuation,
                    'recommendation': recommendation
                })

            except Exception as e:
                # Log but continue with other assets
                analysis_results.append({
                    'symbol': symbol,
                    'name': asset.get('name', symbol),
                    'error': str(e)
                })

        return analysis_results

    def calculate_cost_of_equity(
        self,
        beta: float,
        market_risk_premium: float = None
    ) -> float:
        """
        Calculate cost of equity using CAPM.

        Args:
            beta: Company beta
            market_risk_premium: Market risk premium (Rm - Rf)

        Returns:
            Cost of equity as decimal
        """
        if market_risk_premium is None:
            market_return = self._get_market_expected_return()
            market_risk_premium = market_return - self.risk_free_rate

        return self.risk_free_rate + beta * market_risk_premium

    def _get_market_expected_return(self) -> float:
        """
        Get expected market return based on historical data.

        Returns:
            Expected annual market return
        """
        try:
            import yfinance as yf

            # Get 10-year historical data
            market_data = yf.download(self.market_symbol, period='10y', progress=False)

            if market_data.empty:
                return 0.10  # Default 10% historical average

            returns = market_data['Adj Close'].pct_change().dropna()

            # Calculate annualized return
            daily_mean = returns.mean()
            annual_return = (1 + daily_mean) ** 252 - 1

            return round(float(annual_return), 4)

        except:
            # Default to historical average if data unavailable
            return 0.10

    def _determine_valuation(self, alpha: float) -> str:
        """
        Determine asset valuation based on alpha.

        Args:
            alpha: Jensen's alpha

        Returns:
            Valuation status string
        """
        if alpha > 0.05:
            return 'significantly_undervalued'
        elif alpha > 0.02:
            return 'undervalued'
        elif alpha < -0.05:
            return 'significantly_overvalued'
        elif alpha < -0.02:
            return 'overvalued'
        else:
            return 'fairly_valued'

    def _generate_recommendation(self, alpha: float, beta: float) -> str:
        """
        Generate investment recommendation based on CAPM analysis.

        Args:
            alpha: Jensen's alpha
            beta: Asset beta

        Returns:
            Recommendation string
        """
        if alpha > 0.05:
            return 'strong_buy'
        elif alpha > 0.02:
            return 'buy'
        elif alpha < -0.05:
            return 'strong_sell'
        elif alpha < -0.02:
            return 'sell'
        else:
            return 'hold'

    def get_market_data(self, period: str = '1y') -> Dict[str, Any]:
        """
        Get current market data and statistics.

        Args:
            period: Historical period

        Returns:
            Market data dictionary
        """
        try:
            import yfinance as yf

            market = yf.Ticker(self.market_symbol)
            info = market.info

            hist = market.history(period=period)
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                year_start_price = hist['Close'].iloc[0]
                ytd_return = (current_price - year_start_price) / year_start_price
            else:
                current_price = 0
                ytd_return = 0

            return {
                'symbol': self.market_symbol,
                'current_value': float(current_price),
                'ytd_return': float(ytd_return),
                'risk_free_rate': self.risk_free_rate,
                'market_expected_return': self._get_market_expected_return()
            }

        except:
            return {
                'symbol': self.market_symbol,
                'risk_free_rate': self.risk_free_rate,
                'market_expected_return': 0.10
            }
