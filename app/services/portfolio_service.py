"""
Family Office Platform - Portfolio Service

Provides portfolio management, calculations, and analysis functionality.
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple

from flask import current_app

from app import db
from app.models import User, Account, Asset, RealEstate, Transaction
from app.utils.exceptions import CalculationError, ValidationError


class PortfolioService:
    """Service for portfolio management and calculations."""

    def __init__(self, user_id: str = None):
        """
        Initialize portfolio service.

        Args:
            user_id: Optional user ID to scope operations
        """
        self.user_id = user_id
        self._user = None

    @property
    def user(self) -> Optional[User]:
        """Get the user instance."""
        if self._user is None and self.user_id:
            self._user = self._get_user_by_id(self.user_id)
        return self._user

    def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID, handling string to UUID conversion."""
        if not user_id:
            return None
        # Convert string to UUID if needed
        uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        return db.session.get(User, uid)

    def get_portfolio_summary(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary.

        Args:
            user_id: User ID (uses instance user_id if not provided)

        Returns:
            Dictionary with portfolio summary data
        """
        uid = user_id or self.user_id
        if not uid:
            raise ValidationError("User ID is required")

        user = self._get_user_by_id(uid)
        if not user:
            raise ValidationError("User not found")

        # Calculate totals
        total_cash = self._calculate_cash_total(user)
        total_investments = self._calculate_investments_total(user)
        total_real_estate = self._calculate_real_estate_total(user)
        total_vehicles = self._calculate_asset_type_total(user, 'vehicle')
        total_startup_equity = self._calculate_asset_type_total(user, 'startup_equity')
        total_personal_property = self._calculate_asset_type_total(user, 'personal_property')

        total_assets = (
            total_cash + total_investments + total_real_estate +
            total_vehicles + total_startup_equity + total_personal_property
        )

        total_liabilities = self._calculate_liabilities_total(user)
        net_worth = total_assets - total_liabilities

        # Asset allocation
        allocation = {}
        if total_assets > 0:
            allocation = {
                'cash': float(total_cash),
                'investments': float(total_investments),
                'real_estate': float(total_real_estate),
                'vehicles': float(total_vehicles),
                'startup_equity': float(total_startup_equity),
                'personal_property': float(total_personal_property)
            }

        return {
            'user_id': str(uid),
            'net_worth': float(net_worth),
            'total_assets': float(total_assets),
            'total_liabilities': float(total_liabilities),
            'asset_allocation': allocation,
            'breakdown': {
                'cash': float(total_cash),
                'investments': float(total_investments),
                'real_estate': float(total_real_estate),
                'vehicles': float(total_vehicles),
                'startup_equity': float(total_startup_equity),
                'personal_property': float(total_personal_property)
            },
            'last_updated': datetime.utcnow().isoformat()
        }

    def _calculate_cash_total(self, user: User) -> Decimal:
        """Calculate total cash across bank accounts."""
        total = Decimal('0.00')
        for account in user.accounts.filter_by(account_type='bank', is_active=True):
            if account.current_balance:
                total += account.current_balance
        return total

    def _calculate_investments_total(self, user: User) -> Decimal:
        """Calculate total investment value."""
        total = Decimal('0.00')

        # Investment accounts
        investment_types = ['brokerage', 'retirement', '529', 'ira', '401k']
        for account in user.accounts.filter(Account.account_type.in_(investment_types), Account.is_active == True):
            if account.current_balance:
                total += account.current_balance

        # Individual assets
        asset_types = ['stock', 'bond', 'etf', 'mutual_fund', 'crypto']
        for asset in user.assets.filter(Asset.asset_type.in_(asset_types)):
            if asset.current_value:
                total += asset.current_value

        return total

    def _calculate_real_estate_total(self, user: User) -> Decimal:
        """Calculate total real estate value."""
        total = Decimal('0.00')
        for prop in user.real_estate:
            if prop.current_value:
                total += prop.current_value
        return total

    def _calculate_asset_type_total(self, user: User, asset_type: str) -> Decimal:
        """Calculate total for a specific asset type."""
        total = Decimal('0.00')
        for asset in user.assets.filter_by(asset_type=asset_type):
            if asset.current_value:
                total += asset.current_value
        return total

    def _calculate_liabilities_total(self, user: User) -> Decimal:
        """Calculate total liabilities."""
        total = Decimal('0.00')

        # Liability accounts
        for account in user.accounts.filter(Account.account_type.in_(['loan', 'credit_card', 'liability', 'mortgage'])):
            if account.current_balance:
                total += abs(account.current_balance)

        # Mortgage balances on real estate
        for prop in user.real_estate:
            if prop.mortgage_balance:
                total += prop.mortgage_balance

        return total

    def calculate_performance_metrics(self, user_id: str = None, period: str = '1Y') -> Dict[str, Any]:
        """
        Calculate portfolio performance metrics.

        Args:
            user_id: User ID
            period: Time period (1D, 1W, 1M, 3M, 6M, 1Y, 2Y, 5Y, YTD, ALL)

        Returns:
            Dictionary with performance metrics
        """
        uid = user_id or self.user_id
        if not uid:
            raise ValidationError("User ID is required")

        user = self._get_user_by_id(uid)
        if not user:
            raise ValidationError("User not found")

        # Calculate returns for tradeable assets
        total_return = Decimal('0.00')
        total_value = Decimal('0.00')
        total_cost = Decimal('0.00')

        for asset in user.assets:
            if asset.current_value and asset.cost_basis:
                total_value += asset.current_value
                total_cost += asset.cost_basis

        if total_cost > 0:
            total_return = ((total_value - total_cost) / total_cost)

        # Approximate benchmark (S&P 500 historical average)
        benchmark_return = Decimal('0.10')  # 10% annual

        # Calculate alpha (simplified)
        alpha = total_return - benchmark_return

        # Default beta (would need historical data for accurate calculation)
        beta = Decimal('1.00')

        # Calculate Sharpe ratio (simplified)
        risk_free_rate = Decimal(str(current_app.config.get('DEFAULT_RISK_FREE_RATE', 0.02)))
        volatility = Decimal('0.15')  # Assumed volatility
        sharpe_ratio = Decimal('0.00')
        if volatility > 0:
            sharpe_ratio = (total_return - risk_free_rate) / volatility

        # Calculate max drawdown (simplified - would need time series data)
        max_drawdown = Decimal('-0.10')  # Default assumption

        return {
            'period': period,
            'total_return': float(total_return),
            'benchmark_return': float(benchmark_return),
            'alpha': float(alpha),
            'beta': float(beta),
            'sharpe_ratio': float(sharpe_ratio),
            'volatility': float(volatility),
            'max_drawdown': float(max_drawdown),
            'total_value': float(total_value),
            'total_cost_basis': float(total_cost),
            'unrealized_gain_loss': float(total_value - total_cost),
            'calculated_at': datetime.utcnow().isoformat()
        }

    def get_holdings(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all asset holdings for a user.

        Args:
            user_id: User ID

        Returns:
            List of asset holdings
        """
        uid = user_id or self.user_id
        if not uid:
            raise ValidationError("User ID is required")

        user = self._get_user_by_id(uid)
        if not user:
            raise ValidationError("User not found")

        holdings = []
        for asset in user.assets:
            holdings.append(asset.to_dict())

        return holdings

    def get_accounts(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all accounts for a user.

        Args:
            user_id: User ID

        Returns:
            List of accounts
        """
        uid = user_id or self.user_id
        if not uid:
            raise ValidationError("User ID is required")

        user = self._get_user_by_id(uid)
        if not user:
            raise ValidationError("User not found")

        accounts = []
        for account in user.accounts:
            accounts.append(account.to_dict())

        return accounts

    def get_real_estate(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all real estate holdings for a user.

        Args:
            user_id: User ID

        Returns:
            List of real estate properties
        """
        uid = user_id or self.user_id
        if not uid:
            raise ValidationError("User ID is required")

        user = self._get_user_by_id(uid)
        if not user:
            raise ValidationError("User not found")

        properties = []
        for prop in user.real_estate:
            properties.append(prop.to_dict())

        return properties

    def calculate_rebalancing_plan(
        self,
        user_id: str = None,
        target_allocation: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Calculate portfolio rebalancing recommendations.

        Args:
            user_id: User ID
            target_allocation: Target allocation percentages

        Returns:
            Rebalancing recommendations
        """
        uid = user_id or self.user_id
        if not uid:
            raise ValidationError("User ID is required")

        # Default target allocation for moderate risk
        if target_allocation is None:
            target_allocation = {
                'stocks': 0.60,
                'bonds': 0.25,
                'cash': 0.10,
                'alternatives': 0.05
            }

        summary = self.get_portfolio_summary(uid)
        total_value = Decimal(str(summary['total_assets']))

        # Calculate current allocation percentages
        current_allocation = {}
        for asset_type, value in summary['breakdown'].items():
            if total_value > 0:
                current_allocation[asset_type] = float(Decimal(str(value)) / total_value)

        # Calculate differences
        trades = []
        for asset_type, target_pct in target_allocation.items():
            current_pct = current_allocation.get(asset_type, 0.0)
            diff = target_pct - current_pct

            if abs(diff) > 0.02:  # 2% threshold
                trade_value = float(total_value) * diff
                action = 'buy' if diff > 0 else 'sell'
                trades.append({
                    'asset_type': asset_type,
                    'action': action,
                    'current_allocation': current_pct,
                    'target_allocation': target_pct,
                    'difference': diff,
                    'trade_value': abs(trade_value)
                })

        return {
            'current_allocation': current_allocation,
            'target_allocation': target_allocation,
            'total_portfolio_value': float(total_value),
            'recommended_trades': trades,
            'rebalancing_needed': len(trades) > 0,
            'calculated_at': datetime.utcnow().isoformat()
        }

    def get_portfolio_data(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get comprehensive portfolio data for agent analysis.

        Args:
            user_id: User ID

        Returns:
            Complete portfolio data dictionary
        """
        uid = user_id or self.user_id
        summary = self.get_portfolio_summary(uid)
        performance = self.calculate_performance_metrics(uid)
        holdings = self.get_holdings(uid)
        real_estate = self.get_real_estate(uid)

        return {
            **summary,
            'performance': performance,
            'holdings': holdings,
            'real_estate': real_estate,
            'assets': holdings  # Alias for compatibility
        }

    @staticmethod
    def calculate_total_value(asset_values: List[float]) -> float:
        """
        Calculate sum of asset values.

        Args:
            asset_values: List of asset values

        Returns:
            Total value
        """
        total = Decimal('0.00')
        for value in asset_values:
            total += Decimal(str(value))
        return float(total)
