"""
Family Office Platform - Portfolio API

REST endpoints for portfolio management, holdings, and performance.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from app.services.portfolio_service import PortfolioService
from app.utils.exceptions import ValidationError, CalculationError
from app.utils.formatters import format_portfolio_summary

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/v1/portfolio')


@portfolio_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_portfolio_summary():
    """
    Get comprehensive portfolio summary.

    Returns:
        Portfolio summary with net worth, allocations, and breakdown
    """
    try:
        user_id = get_jwt_identity()
        portfolio_service = PortfolioService(user_id)

        summary = portfolio_service.get_portfolio_summary()
        formatted = format_portfolio_summary(summary)

        return jsonify({
            'status': 'success',
            'data': summary,
            'formatted': formatted,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200

    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@portfolio_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_portfolio_performance():
    """
    Get portfolio performance metrics.

    Query Parameters:
        period: Time period (1D, 1W, 1M, 3M, 6M, 1Y, 2Y, 5Y, YTD, ALL)

    Returns:
        Performance metrics including returns, Sharpe, alpha, beta
    """
    try:
        user_id = get_jwt_identity()
        period = request.args.get('period', '1Y').upper()

        valid_periods = ['1D', '1W', '1M', '3M', '6M', '1Y', '2Y', '5Y', 'YTD', 'ALL']
        if period not in valid_periods:
            return jsonify({
                'status': 'error',
                'message': f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            }), 400

        portfolio_service = PortfolioService(user_id)
        performance = portfolio_service.calculate_performance_metrics(period=period)

        return jsonify({
            'status': 'success',
            'data': performance,
            'period': period
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


@portfolio_bp.route('/holdings', methods=['GET'])
@jwt_required()
def get_holdings():
    """
    Get all asset holdings.

    Query Parameters:
        asset_type: Filter by asset type (stock, bond, etf, etc.)

    Returns:
        List of asset holdings
    """
    try:
        user_id = get_jwt_identity()
        asset_type = request.args.get('asset_type')

        portfolio_service = PortfolioService(user_id)
        holdings = portfolio_service.get_holdings()

        # Filter by type if specified
        if asset_type:
            holdings = [h for h in holdings if h.get('asset_type') == asset_type.lower()]

        return jsonify({
            'status': 'success',
            'data': holdings,
            'count': len(holdings)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@portfolio_bp.route('/accounts', methods=['GET'])
@jwt_required()
def get_accounts():
    """
    Get all financial accounts.

    Query Parameters:
        account_type: Filter by account type (brokerage, retirement, etc.)

    Returns:
        List of accounts
    """
    try:
        user_id = get_jwt_identity()
        account_type = request.args.get('account_type')

        portfolio_service = PortfolioService(user_id)
        accounts = portfolio_service.get_accounts()

        # Filter by type if specified
        if account_type:
            accounts = [a for a in accounts if a.get('account_type') == account_type.lower()]

        return jsonify({
            'status': 'success',
            'data': accounts,
            'count': len(accounts)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@portfolio_bp.route('/real-estate', methods=['GET'])
@jwt_required()
def get_real_estate():
    """
    Get all real estate holdings.

    Query Parameters:
        property_type: Filter by property type (primary, rental, etc.)

    Returns:
        List of real estate properties
    """
    try:
        user_id = get_jwt_identity()
        property_type = request.args.get('property_type')

        portfolio_service = PortfolioService(user_id)
        properties = portfolio_service.get_real_estate()

        # Filter by type if specified
        if property_type:
            properties = [p for p in properties if p.get('property_type') == property_type.lower()]

        return jsonify({
            'status': 'success',
            'data': properties,
            'count': len(properties)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@portfolio_bp.route('/rebalance', methods=['POST'])
@jwt_required()
def calculate_rebalancing():
    """
    Calculate portfolio rebalancing recommendations.

    Request Body (optional):
        target_allocation: Custom target allocation percentages

    Returns:
        Rebalancing recommendations
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        target_allocation = data.get('target_allocation')

        portfolio_service = PortfolioService(user_id)
        rebalancing = portfolio_service.calculate_rebalancing_plan(
            target_allocation=target_allocation
        )

        return jsonify({
            'status': 'success',
            'data': rebalancing
        }), 200

    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@portfolio_bp.route('/allocation', methods=['GET'])
@jwt_required()
def get_allocation():
    """
    Get current asset allocation breakdown.

    Returns:
        Asset allocation percentages and values
    """
    try:
        user_id = get_jwt_identity()

        portfolio_service = PortfolioService(user_id)
        summary = portfolio_service.get_portfolio_summary()

        total_assets = summary.get('total_assets', 0)
        breakdown = summary.get('breakdown', {})

        # Calculate percentages
        allocation = {}
        for asset_type, value in breakdown.items():
            if total_assets > 0:
                allocation[asset_type] = {
                    'value': value,
                    'percentage': round((value / total_assets) * 100, 2)
                }

        return jsonify({
            'status': 'success',
            'data': {
                'total_assets': total_assets,
                'allocation': allocation
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@portfolio_bp.route('/data', methods=['GET'])
@jwt_required()
def get_portfolio_data():
    """
    Get comprehensive portfolio data for analysis.

    Returns:
        Complete portfolio data including summary, performance, and holdings
    """
    try:
        user_id = get_jwt_identity()

        portfolio_service = PortfolioService(user_id)
        data = portfolio_service.get_portfolio_data()

        return jsonify({
            'status': 'success',
            'data': data
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
