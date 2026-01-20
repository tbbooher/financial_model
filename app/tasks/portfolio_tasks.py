"""
Family Office Platform - Portfolio Background Tasks

Celery tasks for portfolio calculations, metrics updates, and rebalancing.
"""

from celery import shared_task
from datetime import datetime
import logging

from app import db
from app.models import User, Asset, Account
from app.services.portfolio_service import PortfolioService
from app.services.data_service import DataService
from app.utils.exceptions import CalculationError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_portfolio_metrics_task(self, user_id: str):
    """
    Calculate and cache portfolio performance metrics.

    Args:
        user_id: User UUID string

    Returns:
        dict: Calculated metrics
    """
    try:
        logger.info(f"Starting portfolio metrics calculation for user {user_id}")

        portfolio_service = PortfolioService(user_id)

        # Calculate metrics for different periods
        periods = ['1D', '1W', '1M', '3M', '6M', '1Y', 'YTD']
        metrics = {}

        for period in periods:
            try:
                metrics[period] = portfolio_service.calculate_performance_metrics(period)
            except CalculationError as e:
                logger.warning(f"Could not calculate metrics for period {period}: {e}")
                metrics[period] = None

        logger.info(f"Portfolio metrics calculation completed for user {user_id}")

        return {
            'user_id': user_id,
            'metrics': metrics,
            'calculated_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Portfolio metrics calculation failed for user {user_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_rebalancing_task(self, user_id: str, target_allocation: dict = None):
    """
    Calculate portfolio rebalancing recommendations.

    Args:
        user_id: User UUID string
        target_allocation: Optional custom target allocation

    Returns:
        dict: Rebalancing recommendations
    """
    try:
        logger.info(f"Starting rebalancing calculation for user {user_id}")

        portfolio_service = PortfolioService(user_id)
        rebalancing_plan = portfolio_service.calculate_rebalancing_plan(target_allocation)

        logger.info(f"Rebalancing calculation completed for user {user_id}")

        return {
            'user_id': user_id,
            'rebalancing_plan': rebalancing_plan,
            'calculated_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Rebalancing calculation failed for user {user_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def update_portfolio_values_task(self, user_id: str = None):
    """
    Update current values for all portfolio assets.

    Args:
        user_id: Optional user UUID to update specific portfolio.
                 If None, updates all users.

    Returns:
        dict: Update results
    """
    try:
        logger.info(f"Starting portfolio value update" +
                   (f" for user {user_id}" if user_id else " for all users"))

        data_service = DataService()

        # Get users to update
        if user_id:
            users = [User.query.get(user_id)]
        else:
            users = User.query.filter_by(is_active=True).all()

        updated_count = 0
        errors = []

        for user in users:
            if not user:
                continue

            try:
                # Get all marketable assets
                assets = Asset.query.filter_by(user_id=user.id).filter(
                    Asset.symbol.isnot(None)
                ).all()

                for asset in assets:
                    try:
                        if asset.asset_type in ['stock', 'etf', 'mutual_fund']:
                            price_data = data_service.get_stock_price(asset.symbol)
                            if price_data and 'price' in price_data:
                                new_value = float(price_data['price']) * float(asset.quantity)
                                asset.current_value = new_value
                                asset.last_updated = datetime.utcnow()
                                updated_count += 1
                    except Exception as e:
                        errors.append({
                            'asset_id': str(asset.id),
                            'symbol': asset.symbol,
                            'error': str(e)
                        })

                db.session.commit()

            except Exception as e:
                errors.append({
                    'user_id': str(user.id),
                    'error': str(e)
                })
                db.session.rollback()

        logger.info(f"Portfolio value update completed. Updated {updated_count} assets.")

        return {
            'updated_count': updated_count,
            'errors': errors,
            'completed_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Portfolio value update failed: {e}")
        raise self.retry(exc=e)


@shared_task
def calculate_risk_metrics_task(user_id: str):
    """
    Calculate comprehensive risk metrics for a portfolio.

    Args:
        user_id: User UUID string

    Returns:
        dict: Risk metrics
    """
    try:
        logger.info(f"Starting risk metrics calculation for user {user_id}")

        from app.services.risk_service import RiskService

        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        risk_service = RiskService(portfolio_data)

        metrics = {
            'var_95': risk_service.calculate_var(confidence_level=0.95),
            'var_99': risk_service.calculate_var(confidence_level=0.99),
            'cvar_95': risk_service.calculate_cvar(confidence_level=0.95),
            'sharpe_ratio': risk_service.calculate_sharpe_ratio(),
            'max_drawdown': risk_service.calculate_max_drawdown(),
            'volatility': risk_service.calculate_volatility()
        }

        logger.info(f"Risk metrics calculation completed for user {user_id}")

        return {
            'user_id': user_id,
            'risk_metrics': metrics,
            'calculated_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Risk metrics calculation failed for user {user_id}: {e}")
        raise


@shared_task
def run_monte_carlo_task(user_id: str, simulations: int = 10000, years: float = 1.0):
    """
    Run Monte Carlo simulation for portfolio.

    Args:
        user_id: User UUID string
        simulations: Number of simulation runs
        years: Time horizon in years

    Returns:
        dict: Simulation results
    """
    try:
        logger.info(f"Starting Monte Carlo simulation for user {user_id}")

        from app.services.risk_service import RiskService

        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        risk_service = RiskService(portfolio_data)
        results = risk_service.monte_carlo_simulation(
            time_horizon_years=years,
            simulations=simulations
        )

        logger.info(f"Monte Carlo simulation completed for user {user_id}")

        return {
            'user_id': user_id,
            'simulation_results': results,
            'parameters': {
                'simulations': simulations,
                'years': years
            },
            'calculated_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Monte Carlo simulation failed for user {user_id}: {e}")
        raise
