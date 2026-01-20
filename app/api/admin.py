"""
Family Office Platform - Admin API

REST endpoints for administrative functions, data sync, and system health.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from app import db
from app.models import User, Account, Asset, RealEstate, Transaction, AgentTask
from app.services.data_service import DataService

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


@admin_bp.route('/health', methods=['GET'])
def health_check():
    """
    System health check endpoint.

    Returns:
        Health status of various system components
    """
    health = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'components': {}
    }

    # Check database
    try:
        db.session.execute(db.text('SELECT 1'))
        health['components']['database'] = 'healthy'
    except Exception as e:
        health['components']['database'] = 'unhealthy'
        health['status'] = 'degraded'

    # Check Redis (if available)
    try:
        from flask import current_app
        import redis
        r = redis.from_url(current_app.config.get('REDIS_URL', 'redis://localhost:6379/0'))
        r.ping()
        health['components']['redis'] = 'healthy'
    except Exception:
        health['components']['redis'] = 'unavailable'

    return jsonify(health), 200 if health['status'] == 'healthy' else 503


@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Get system statistics.

    Returns:
        User, asset, and task statistics
    """
    try:
        stats = {
            'users': {
                'total': User.query.count(),
                'active': User.query.filter_by(is_active=True).count()
            },
            'accounts': {
                'total': Account.query.count()
            },
            'assets': {
                'total': Asset.query.count()
            },
            'real_estate': {
                'total': RealEstate.query.count()
            },
            'transactions': {
                'total': Transaction.query.count()
            },
            'agent_tasks': {
                'total': AgentTask.query.count(),
                'pending': AgentTask.query.filter_by(status='pending').count(),
                'completed': AgentTask.query.filter_by(status='completed').count(),
                'failed': AgentTask.query.filter_by(status='failed').count()
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        return jsonify({
            'status': 'success',
            'data': stats
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@admin_bp.route('/sync', methods=['POST'])
@jwt_required()
def trigger_sync():
    """
    Trigger portfolio data synchronization.

    Returns:
        Sync results
    """
    try:
        user_id = get_jwt_identity()

        data_service = DataService()
        results = data_service.sync_portfolio_prices(user_id)

        return jsonify({
            'status': 'success',
            'message': 'Sync completed',
            'data': results
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@admin_bp.route('/clear-cache', methods=['POST'])
@jwt_required()
def clear_cache():
    """
    Clear data service cache.

    Returns:
        Success message
    """
    try:
        data_service = DataService()
        data_service.clear_cache()

        return jsonify({
            'status': 'success',
            'message': 'Cache cleared'
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """
    List all users (admin only - implement RBAC in production).

    Query Parameters:
        limit: Maximum users to return
        offset: Pagination offset

    Returns:
        List of users
    """
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        users = User.query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
        total = User.query.count()

        return jsonify({
            'status': 'success',
            'data': [user.to_dict() for user in users],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@admin_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id: str):
    """
    Get specific user details.

    Path Parameters:
        user_id: User UUID

    Returns:
        User details
    """
    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        return jsonify({
            'status': 'success',
            'data': user.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@admin_bp.route('/tasks', methods=['GET'])
@jwt_required()
def list_all_tasks():
    """
    List all agent tasks across all users.

    Query Parameters:
        status: Filter by status
        agent_type: Filter by agent type
        limit: Maximum tasks to return

    Returns:
        List of agent tasks
    """
    try:
        query = AgentTask.query

        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)

        agent_type = request.args.get('agent_type')
        if agent_type:
            query = query.filter_by(agent_type=agent_type)

        limit = int(request.args.get('limit', 50))
        tasks = query.order_by(AgentTask.created_at.desc()).limit(limit).all()

        return jsonify({
            'status': 'success',
            'data': [task.to_dict() for task in tasks],
            'count': len(tasks)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@admin_bp.route('/cleanup-tasks', methods=['POST'])
@jwt_required()
def cleanup_tasks():
    """
    Clean up old completed/failed tasks.

    Request Body:
        days_old: Delete tasks older than this many days (default 30)

    Returns:
        Number of tasks deleted
    """
    try:
        data = request.get_json() or {}
        days_old = int(data.get('days_old', 30))

        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)

        deleted = AgentTask.query.filter(
            AgentTask.created_at < cutoff,
            AgentTask.status.in_(['completed', 'failed', 'cancelled'])
        ).delete()

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Deleted {deleted} old tasks',
            'deleted_count': deleted
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@admin_bp.route('/config', methods=['GET'])
@jwt_required()
def get_config():
    """
    Get application configuration (non-sensitive).

    Returns:
        Configuration values
    """
    try:
        from flask import current_app

        config = {
            'environment': current_app.config.get('FLASK_ENV', 'development'),
            'debug': current_app.debug,
            'default_risk_free_rate': current_app.config.get('DEFAULT_RISK_FREE_RATE'),
            'default_market_symbol': current_app.config.get('DEFAULT_MARKET_SYMBOL'),
            'portfolio_update_interval': current_app.config.get('PORTFOLIO_UPDATE_INTERVAL'),
            'agent_confidence_threshold': current_app.config.get('AGENT_CONFIDENCE_THRESHOLD'),
            'max_agent_processing_time': current_app.config.get('MAX_AGENT_PROCESSING_TIME'),
            'rate_limit_default': current_app.config.get('RATELIMIT_DEFAULT'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        return jsonify({
            'status': 'success',
            'data': config
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
