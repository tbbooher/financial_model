"""
Family Office Platform - Data Synchronization Tasks

Celery tasks for synchronizing external market data, stock prices,
and economic indicators.
"""

from celery import shared_task
from datetime import datetime
import logging

from app import db
from app.models import Asset, User
from app.services.data_service import DataService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def sync_stock_prices_task(self, symbols: list = None):
    """
    Synchronize stock prices for specified symbols or all tracked symbols.

    Args:
        symbols: Optional list of stock symbols. If None, syncs all.

    Returns:
        dict: Sync results
    """
    try:
        logger.info("Starting stock price synchronization")

        data_service = DataService()

        # Get symbols to sync
        if symbols is None:
            # Get all unique symbols from assets
            assets = Asset.query.filter(
                Asset.symbol.isnot(None),
                Asset.asset_type.in_(['stock', 'etf', 'mutual_fund'])
            ).all()
            symbols = list(set(asset.symbol for asset in assets if asset.symbol))

        results = {
            'synced': [],
            'failed': [],
            'total_symbols': len(symbols)
        }

        for symbol in symbols:
            try:
                price_data = data_service.get_stock_price(symbol)

                if price_data and 'price' in price_data:
                    # Update all assets with this symbol
                    assets = Asset.query.filter_by(symbol=symbol).all()
                    for asset in assets:
                        new_value = float(price_data['price']) * float(asset.quantity)
                        asset.current_value = new_value
                        asset.last_updated = datetime.utcnow()

                    results['synced'].append({
                        'symbol': symbol,
                        'price': price_data['price'],
                        'assets_updated': len(assets)
                    })
                else:
                    results['failed'].append({
                        'symbol': symbol,
                        'error': 'No price data returned'
                    })

            except Exception as e:
                results['failed'].append({
                    'symbol': symbol,
                    'error': str(e)
                })

        db.session.commit()

        logger.info(f"Stock price sync completed. Synced: {len(results['synced'])}, "
                   f"Failed: {len(results['failed'])}")

        return {
            'results': results,
            'completed_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Stock price synchronization failed: {e}")
        db.session.rollback()
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_market_data_task(self):
    """
    Synchronize market index data and sector performance.

    Returns:
        dict: Market data sync results
    """
    try:
        logger.info("Starting market data synchronization")

        data_service = DataService()

        # Sync market indices
        market_data = data_service.get_market_data()

        # Sync sector performance
        sector_data = data_service.get_sector_performance()

        results = {
            'market_indices': market_data,
            'sector_performance': sector_data,
            'synced_at': datetime.utcnow().isoformat()
        }

        logger.info("Market data synchronization completed")

        return results

    except Exception as e:
        logger.error(f"Market data synchronization failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_economic_indicators_task(self):
    """
    Synchronize economic indicators data.

    Returns:
        dict: Economic indicators data
    """
    try:
        logger.info("Starting economic indicators synchronization")

        data_service = DataService()

        indicators = data_service.get_economic_indicators()

        results = {
            'indicators': indicators,
            'synced_at': datetime.utcnow().isoformat()
        }

        logger.info("Economic indicators synchronization completed")

        return results

    except Exception as e:
        logger.error(f"Economic indicators synchronization failed: {e}")
        raise self.retry(exc=e)


@shared_task
def sync_historical_data_task(symbol: str, period: str = '2y'):
    """
    Synchronize historical price data for a symbol.

    Args:
        symbol: Stock/ETF symbol
        period: Historical period (1mo, 3mo, 6mo, 1y, 2y, 5y)

    Returns:
        dict: Historical data sync results
    """
    try:
        logger.info(f"Starting historical data sync for {symbol}, period: {period}")

        data_service = DataService()

        historical_data = data_service.get_historical_prices(
            symbol=symbol,
            period=period,
            interval='1d'
        )

        results = {
            'symbol': symbol,
            'period': period,
            'data_points': len(historical_data.get('prices', [])),
            'synced_at': datetime.utcnow().isoformat()
        }

        logger.info(f"Historical data sync completed for {symbol}")

        return results

    except Exception as e:
        logger.error(f"Historical data sync failed for {symbol}: {e}")
        raise


@shared_task
def sync_all_portfolio_prices_task(user_id: str):
    """
    Synchronize all asset prices for a user's portfolio.

    Args:
        user_id: User UUID string

    Returns:
        dict: Sync results
    """
    try:
        logger.info(f"Starting portfolio price sync for user {user_id}")

        data_service = DataService()
        results = data_service.sync_portfolio_prices(user_id)

        logger.info(f"Portfolio price sync completed for user {user_id}")

        return {
            'user_id': user_id,
            'results': results,
            'synced_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Portfolio price sync failed for user {user_id}: {e}")
        raise


@shared_task
def cleanup_stale_cache_task():
    """
    Clean up stale cached data.

    Returns:
        dict: Cleanup results
    """
    try:
        logger.info("Starting stale cache cleanup")

        data_service = DataService()
        data_service.clear_cache()

        logger.info("Stale cache cleanup completed")

        return {
            'status': 'success',
            'cleaned_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        raise


@shared_task
def validate_data_integrity_task():
    """
    Validate data integrity across the system.

    Returns:
        dict: Validation results
    """
    try:
        logger.info("Starting data integrity validation")

        issues = []

        # Check for assets without prices
        stale_assets = Asset.query.filter(
            Asset.current_value.is_(None)
        ).all()

        if stale_assets:
            issues.append({
                'type': 'missing_value',
                'count': len(stale_assets),
                'description': 'Assets without current value'
            })

        # Check for users without any assets
        users_without_assets = db.session.query(User).outerjoin(Asset).filter(
            Asset.id.is_(None)
        ).all()

        if users_without_assets:
            issues.append({
                'type': 'empty_portfolio',
                'count': len(users_without_assets),
                'description': 'Users without any assets'
            })

        results = {
            'status': 'healthy' if not issues else 'issues_found',
            'issues': issues,
            'validated_at': datetime.utcnow().isoformat()
        }

        logger.info(f"Data integrity validation completed. Issues: {len(issues)}")

        return results

    except Exception as e:
        logger.error(f"Data integrity validation failed: {e}")
        raise
