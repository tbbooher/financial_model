"""
Family Office Platform - Data Service

Provides external data integration for market data, stock prices,
and portfolio synchronization.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

from flask import current_app

from app import db
from app.models import Asset
from app.utils.exceptions import DataIntegrationError

logger = logging.getLogger(__name__)


class DataService:
    """
    Service for external data integration.

    Provides:
    - Stock price retrieval
    - Market data
    - Portfolio price synchronization
    - Historical data
    """

    def __init__(self):
        """Initialize data service."""
        self._cache = {}
        self._cache_expiry = {}
        self._cache_duration = timedelta(minutes=5)

    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock price and basic info.

        Args:
            symbol: Stock/ETF symbol

        Returns:
            Dictionary with price data
        """
        cache_key = f"price_{symbol}"

        # Check cache
        if self._is_cached(cache_key):
            return self._cache[cache_key]

        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current price
            hist = ticker.history(period='1d')
            current_price = float(hist['Close'].iloc[-1]) if not hist.empty else 0.0

            data = {
                'symbol': symbol.upper(),
                'current_price': current_price,
                'previous_close': info.get('previousClose', 0),
                'open': info.get('open', 0),
                'day_high': info.get('dayHigh', 0),
                'day_low': info.get('dayLow', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE'),
                'dividend_yield': info.get('dividendYield'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'name': info.get('shortName', symbol),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange'),
                'last_updated': datetime.utcnow().isoformat()
            }

            # Calculate daily change
            if data['previous_close'] and data['previous_close'] > 0:
                data['change'] = current_price - data['previous_close']
                data['change_percent'] = (data['change'] / data['previous_close']) * 100
            else:
                data['change'] = 0.0
                data['change_percent'] = 0.0

            self._set_cache(cache_key, data)
            return data

        except ImportError:
            raise DataIntegrationError(
                "yfinance library not available",
                service='yfinance'
            )
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise DataIntegrationError(
                f"Failed to retrieve price for {symbol}: {str(e)}",
                service='yfinance'
            )

    def get_historical_prices(
        self,
        symbol: str,
        period: str = '1y',
        interval: str = '1d'
    ) -> Dict[str, Any]:
        """
        Get historical price data.

        Args:
            symbol: Stock/ETF symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            Dictionary with historical data
        """
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                return {'error': f'No historical data for {symbol}'}

            # Convert to serializable format
            data = {
                'symbol': symbol.upper(),
                'period': period,
                'interval': interval,
                'data_points': len(hist),
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'open': hist['Open'].tolist(),
                'high': hist['High'].tolist(),
                'low': hist['Low'].tolist(),
                'close': hist['Close'].tolist(),
                'volume': hist['Volume'].tolist(),
                'start_date': hist.index[0].strftime('%Y-%m-%d'),
                'end_date': hist.index[-1].strftime('%Y-%m-%d')
            }

            # Calculate returns
            if len(hist) > 1:
                data['total_return'] = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                data['daily_returns'] = hist['Close'].pct_change().dropna().tolist()

            return data

        except ImportError:
            raise DataIntegrationError(
                "yfinance library not available",
                service='yfinance'
            )
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            raise DataIntegrationError(
                f"Failed to retrieve historical data for {symbol}: {str(e)}",
                service='yfinance'
            )

    def get_market_data(self) -> Dict[str, Any]:
        """
        Get major market indices data.

        Returns:
            Dictionary with market data
        """
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^RUT': 'Russell 2000',
            '^VIX': 'VIX'
        }

        market_data = {
            'indices': [],
            'last_updated': datetime.utcnow().isoformat()
        }

        for symbol, name in indices.items():
            try:
                data = self.get_stock_price(symbol)
                market_data['indices'].append({
                    'symbol': symbol,
                    'name': name,
                    'price': data.get('current_price', 0),
                    'change': data.get('change', 0),
                    'change_percent': data.get('change_percent', 0)
                })
            except Exception as e:
                logger.warning(f"Failed to get data for {symbol}: {e}")

        return market_data

    def sync_portfolio_prices(self, user_id: str) -> Dict[str, Any]:
        """
        Synchronize all portfolio asset prices.

        Args:
            user_id: User ID

        Returns:
            Dictionary with sync results
        """
        from app.models import Asset, User

        user = User.query.get(user_id)
        if not user:
            raise DataIntegrationError("User not found", service='portfolio_sync')

        results = {
            'updated': 0,
            'failed': 0,
            'skipped': 0,
            'assets': [],
            'sync_time': datetime.utcnow().isoformat()
        }

        for asset in user.assets:
            if not asset.symbol or asset.asset_type not in ['stock', 'etf', 'mutual_fund', 'crypto']:
                results['skipped'] += 1
                continue

            try:
                price_data = self.get_stock_price(asset.symbol)
                new_price = Decimal(str(price_data['current_price']))

                # Update asset
                old_value = asset.current_value
                asset.current_price = new_price
                asset.current_value = asset.quantity * new_price
                asset.last_updated = datetime.utcnow()

                results['updated'] += 1
                results['assets'].append({
                    'symbol': asset.symbol,
                    'old_price': float(asset.current_price) if asset.current_price else 0,
                    'new_price': float(new_price),
                    'old_value': float(old_value) if old_value else 0,
                    'new_value': float(asset.current_value)
                })

            except Exception as e:
                logger.error(f"Failed to sync {asset.symbol}: {e}")
                results['failed'] += 1

        # Commit changes
        db.session.commit()

        # Update user net worth
        user.update_net_worth()
        db.session.commit()

        return results

    def get_sector_performance(self) -> Dict[str, Any]:
        """
        Get sector performance data.

        Returns:
            Dictionary with sector performance
        """
        sector_etfs = {
            'XLK': 'Technology',
            'XLF': 'Financials',
            'XLV': 'Healthcare',
            'XLE': 'Energy',
            'XLY': 'Consumer Discretionary',
            'XLP': 'Consumer Staples',
            'XLI': 'Industrials',
            'XLB': 'Materials',
            'XLU': 'Utilities',
            'XLRE': 'Real Estate',
            'XLC': 'Communications'
        }

        sectors = []
        for symbol, name in sector_etfs.items():
            try:
                data = self.get_stock_price(symbol)
                sectors.append({
                    'symbol': symbol,
                    'sector': name,
                    'price': data.get('current_price', 0),
                    'change_percent': data.get('change_percent', 0)
                })
            except Exception:
                pass

        # Sort by performance
        sectors.sort(key=lambda x: x['change_percent'], reverse=True)

        return {
            'sectors': sectors,
            'best_performer': sectors[0] if sectors else None,
            'worst_performer': sectors[-1] if sectors else None,
            'last_updated': datetime.utcnow().isoformat()
        }

    def get_economic_indicators(self) -> Dict[str, Any]:
        """
        Get basic economic indicators.

        Returns:
            Dictionary with economic data
        """
        # Treasury yields (approximated via ETFs)
        indicators = {
            'treasury_10y': {
                'name': '10-Year Treasury Yield',
                'value': None
            },
            'treasury_2y': {
                'name': '2-Year Treasury Yield',
                'value': None
            },
            'vix': {
                'name': 'VIX (Volatility Index)',
                'value': None
            }
        }

        try:
            vix_data = self.get_stock_price('^VIX')
            indicators['vix']['value'] = vix_data.get('current_price')
        except:
            pass

        try:
            # 10-year treasury rate (approximation)
            tnx_data = self.get_stock_price('^TNX')
            indicators['treasury_10y']['value'] = tnx_data.get('current_price')
        except:
            pass

        return {
            'indicators': indicators,
            'last_updated': datetime.utcnow().isoformat()
        }

    def _is_cached(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        if key not in self._cache_expiry:
            return False
        return datetime.utcnow() < self._cache_expiry[key]

    def _set_cache(self, key: str, data: Any):
        """Set cache with expiry."""
        self._cache[key] = data
        self._cache_expiry[key] = datetime.utcnow() + self._cache_duration

    def clear_cache(self):
        """Clear all cached data."""
        self._cache = {}
        self._cache_expiry = {}
