"""
Family Office Platform - Analytics API

REST endpoints for financial analytics, CAPM analysis, risk metrics,
and Monte Carlo simulations.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.services.portfolio_service import PortfolioService
from app.services.capm_service import CAPMService
from app.services.risk_service import RiskService
from app.services.data_service import DataService
from app.utils.exceptions import ValidationError, CalculationError

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')


@analytics_bp.route('/capm', methods=['GET'])
@jwt_required()
def get_capm_analysis():
    """
    Get CAPM analysis for portfolio.

    Returns:
        Portfolio beta, expected returns, security market line, and asset analysis
    """
    try:
        user_id = get_jwt_identity()

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Perform CAPM analysis
        capm_service = CAPMService()

        analysis = {
            'portfolio_beta': capm_service.calculate_portfolio_beta(portfolio_data),
            'expected_return': capm_service.calculate_expected_return(
                capm_service.calculate_portfolio_beta(portfolio_data)
            ),
            'security_market_line': capm_service.generate_security_market_line(),
            'asset_analysis': capm_service.analyze_asset_pricing(portfolio_data),
            'market_data': capm_service.get_market_data(),
            'risk_free_rate': capm_service.risk_free_rate,
            'calculated_at': datetime.utcnow().isoformat()
        }

        return jsonify({
            'status': 'success',
            'data': analysis
        }), 200

    except CalculationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@analytics_bp.route('/risk', methods=['GET'])
@jwt_required()
def get_risk_analysis():
    """
    Get comprehensive risk analysis.

    Query Parameters:
        confidence: VaR confidence level (default 0.95)
        horizon: Time horizon in days (default 1)

    Returns:
        VaR, CVaR, volatility, Sharpe ratio, max drawdown
    """
    try:
        user_id = get_jwt_identity()

        confidence = float(request.args.get('confidence', 0.95))
        horizon = int(request.args.get('horizon', 1))

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Perform risk analysis
        risk_service = RiskService(portfolio_data)

        analysis = {
            'var': risk_service.calculate_var(
                confidence_level=confidence,
                time_horizon=horizon
            ),
            'cvar': risk_service.calculate_cvar(
                confidence_level=confidence,
                time_horizon=horizon
            ),
            'sharpe_ratio': risk_service.calculate_sharpe_ratio(),
            'max_drawdown': risk_service.calculate_max_drawdown(),
            'parameters': {
                'confidence_level': confidence,
                'time_horizon_days': horizon
            },
            'calculated_at': datetime.utcnow().isoformat()
        }

        return jsonify({
            'status': 'success',
            'data': analysis
        }), 200

    except CalculationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@analytics_bp.route('/monte-carlo', methods=['GET'])
@jwt_required()
def get_monte_carlo():
    """
    Run Monte Carlo simulation.

    Query Parameters:
        years: Time horizon in years (default 1)
        simulations: Number of simulations (default 10000)

    Returns:
        Simulation results with percentiles and statistics
    """
    try:
        user_id = get_jwt_identity()

        years = float(request.args.get('years', 1.0))
        simulations = int(request.args.get('simulations', 10000))

        # Limit simulations
        if simulations > 100000:
            simulations = 100000

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Run simulation
        risk_service = RiskService(portfolio_data)
        results = risk_service.monte_carlo_simulation(
            time_horizon_years=years,
            simulations=simulations
        )

        return jsonify({
            'status': 'success',
            'data': results
        }), 200

    except CalculationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@analytics_bp.route('/stress-test', methods=['GET'])
@jwt_required()
def get_stress_test():
    """
    Run portfolio stress testing.

    Returns:
        Stress test results for various market scenarios
    """
    try:
        user_id = get_jwt_identity()

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Run stress test
        risk_service = RiskService(portfolio_data)
        results = risk_service.stress_test()

        return jsonify({
            'status': 'success',
            'data': results
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@analytics_bp.route('/correlation', methods=['GET'])
@jwt_required()
def get_correlation():
    """
    Get correlation analysis between portfolio assets.

    Returns:
        Correlation matrix and diversification metrics
    """
    try:
        user_id = get_jwt_identity()

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Run correlation analysis
        risk_service = RiskService(portfolio_data)
        results = risk_service.correlation_analysis()

        return jsonify({
            'status': 'success',
            'data': results
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@analytics_bp.route('/market-data', methods=['GET'])
@jwt_required()
def get_market_data():
    """
    Get current market data and indices.

    Returns:
        Major market indices and sector performance
    """
    try:
        data_service = DataService()

        market = data_service.get_market_data()
        sectors = data_service.get_sector_performance()
        economic = data_service.get_economic_indicators()

        return jsonify({
            'status': 'success',
            'data': {
                'market_indices': market,
                'sector_performance': sectors,
                'economic_indicators': economic
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@analytics_bp.route('/stock/<symbol>', methods=['GET'])
@jwt_required()
def get_stock_data(symbol: str):
    """
    Get data for a specific stock/ETF.

    Path Parameters:
        symbol: Stock/ETF symbol

    Returns:
        Current price and basic info
    """
    try:
        data_service = DataService()
        data = data_service.get_stock_price(symbol)

        return jsonify({
            'status': 'success',
            'data': data
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@analytics_bp.route('/stock/<symbol>/history', methods=['GET'])
@jwt_required()
def get_stock_history(symbol: str):
    """
    Get historical data for a stock/ETF.

    Path Parameters:
        symbol: Stock/ETF symbol

    Query Parameters:
        period: Time period (1mo, 3mo, 6mo, 1y, 2y, 5y)
        interval: Data interval (1d, 1wk, 1mo)

    Returns:
        Historical price data
    """
    try:
        period = request.args.get('period', '1y')
        interval = request.args.get('interval', '1d')

        data_service = DataService()
        data = data_service.get_historical_prices(
            symbol=symbol,
            period=period,
            interval=interval
        )

        return jsonify({
            'status': 'success',
            'data': data
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@analytics_bp.route('/beta/<symbol>', methods=['GET'])
@jwt_required()
def get_asset_beta(symbol: str):
    """
    Calculate beta for a specific asset.

    Path Parameters:
        symbol: Stock/ETF symbol

    Query Parameters:
        period: Historical period for calculation (default 2y)

    Returns:
        Beta coefficient and expected return
    """
    try:
        period = request.args.get('period', '2y')

        capm_service = CAPMService()
        beta = capm_service.calculate_beta(symbol, period)
        expected_return = capm_service.calculate_expected_return(beta)

        return jsonify({
            'status': 'success',
            'data': {
                'symbol': symbol.upper(),
                'beta': beta,
                'expected_return': expected_return,
                'risk_free_rate': capm_service.risk_free_rate,
                'market_symbol': capm_service.market_symbol,
                'period': period
            }
        }), 200

    except CalculationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
