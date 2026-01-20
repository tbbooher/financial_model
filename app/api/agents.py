"""
Family Office Platform - Agents API

REST endpoints for AI agent interactions and task management.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid as uuid_module

from app.services.portfolio_service import PortfolioService
from app.agents.agent_manager import AgentManager
from app.utils.exceptions import ValidationError, AgentError

agents_bp = Blueprint('agents', __name__, url_prefix='/api/v1/agents')


@agents_bp.route('/', methods=['GET'])
@jwt_required()
def list_agents():
    """
    List all available agents.

    Returns:
        List of agents with descriptions
    """
    agents = AgentManager.get_available_agents()

    return jsonify({
        'status': 'success',
        'data': agents
    }), 200


@agents_bp.route('/<agent_type>/analyze', methods=['POST'])
@jwt_required()
def run_agent_analysis(agent_type: str):
    """
    Run analysis using specified agent.

    Path Parameters:
        agent_type: Type of agent (cfa, cfp, cio, accountant, quant_risk, quant_strategy)

    Request Body (optional):
        task_type: Type of analysis task
        include_recommendations: Whether to include recommendations

    Returns:
        Agent analysis results
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        task_type = data.get('task_type', 'full_analysis')

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Run analysis
        manager = AgentManager(user_id=user_id, portfolio_data=portfolio_data)
        response = manager.run_analysis(
            agent_type=agent_type,
            task_type=task_type,
            save_task=True
        )

        return jsonify({
            'status': 'success',
            'data': response.to_dict()
        }), 200

    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except AgentError as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'agent_type': e.agent_type if hasattr(e, 'agent_type') else None
        }), 422
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Agent analysis failed: {str(e)}'
        }), 500


@agents_bp.route('/analyze-all', methods=['POST'])
@jwt_required()
def run_all_analyses():
    """
    Run analysis using all available agents.

    Returns:
        Analysis results from all agents
    """
    try:
        user_id = get_jwt_identity()

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Run all analyses
        manager = AgentManager(user_id=user_id, portfolio_data=portfolio_data)
        results = manager.run_all_analyses(save_tasks=True)

        # Convert responses to dict
        response_data = {}
        for agent_type, response in results.items():
            response_data[agent_type] = response.to_dict()

        return jsonify({
            'status': 'success',
            'data': response_data,
            'agents_run': list(results.keys())
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Analysis failed: {str(e)}'
        }), 500


@agents_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """
    Get consolidated recommendations from all agents.

    Query Parameters:
        agents: Comma-separated list of agent types (optional)
        max: Maximum number of recommendations

    Returns:
        Prioritized list of recommendations
    """
    try:
        user_id = get_jwt_identity()

        # Parse parameters
        agents_param = request.args.get('agents')
        agent_types = agents_param.split(',') if agents_param else None
        max_recs = int(request.args.get('max', 20))

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        # Get consolidated recommendations
        manager = AgentManager(user_id=user_id, portfolio_data=portfolio_data)
        recommendations = manager.get_consolidated_recommendations(
            agent_types=agent_types,
            max_recommendations=max_recs
        )

        return jsonify({
            'status': 'success',
            'data': recommendations,
            'count': len(recommendations)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@agents_bp.route('/tasks', methods=['GET'])
@jwt_required()
def list_tasks():
    """
    List agent tasks for current user.

    Query Parameters:
        status: Filter by status (pending, processing, completed, failed)
        agent_type: Filter by agent type
        limit: Maximum number of tasks to return

    Returns:
        List of agent tasks
    """
    try:
        user_id = get_jwt_identity()
        user_uuid = uuid_module.UUID(user_id)

        from app.models import AgentTask

        # Build query
        query = AgentTask.query.filter_by(user_id=user_uuid)

        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)

        agent_type = request.args.get('agent_type')
        if agent_type:
            query = query.filter_by(agent_type=agent_type)

        limit = int(request.args.get('limit', 20))
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


@agents_bp.route('/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id: str):
    """
    Get details of a specific task.

    Path Parameters:
        task_id: Task UUID

    Returns:
        Task details including results
    """
    try:
        user_id = get_jwt_identity()

        manager = AgentManager(user_id=user_id)
        task = manager.get_task(task_id)

        if not task:
            return jsonify({
                'status': 'error',
                'message': 'Task not found'
            }), 404

        # Verify ownership
        if str(task.user_id) != user_id:
            return jsonify({
                'status': 'error',
                'message': 'Access denied'
            }), 403

        return jsonify({
            'status': 'success',
            'data': task.to_dict(include_full_output=True)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@agents_bp.route('/tasks/<task_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_task(task_id: str):
    """
    Cancel a pending or processing task.

    Path Parameters:
        task_id: Task UUID

    Returns:
        Success or error message
    """
    try:
        user_id = get_jwt_identity()

        manager = AgentManager(user_id=user_id)
        task = manager.get_task(task_id)

        if not task:
            return jsonify({
                'status': 'error',
                'message': 'Task not found'
            }), 404

        # Verify ownership
        if str(task.user_id) != user_id:
            return jsonify({
                'status': 'error',
                'message': 'Access denied'
            }), 403

        success = manager.cancel_task(task_id)

        if success:
            return jsonify({
                'status': 'success',
                'message': 'Task cancelled'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Cannot cancel task in current state'
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@agents_bp.route('/tasks/<task_id>/retry', methods=['POST'])
@jwt_required()
def retry_task(task_id: str):
    """
    Retry a failed task.

    Path Parameters:
        task_id: Task UUID

    Returns:
        New analysis results
    """
    try:
        user_id = get_jwt_identity()

        # Get portfolio data
        portfolio_service = PortfolioService(user_id)
        portfolio_data = portfolio_service.get_portfolio_data()

        manager = AgentManager(user_id=user_id, portfolio_data=portfolio_data)
        task = manager.get_task(task_id)

        if not task:
            return jsonify({
                'status': 'error',
                'message': 'Task not found'
            }), 404

        # Verify ownership
        if str(task.user_id) != user_id:
            return jsonify({
                'status': 'error',
                'message': 'Access denied'
            }), 403

        response = manager.retry_task(task_id)

        if response:
            return jsonify({
                'status': 'success',
                'data': response.to_dict()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Cannot retry task - max retries exceeded or not in failed state'
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@agents_bp.route('/status', methods=['GET'])
@jwt_required()
def get_agent_status():
    """
    Get status of agent system.

    Returns:
        Agent system status and recent tasks
    """
    try:
        user_id = get_jwt_identity()

        manager = AgentManager(user_id=user_id)
        status = manager.get_agent_status()

        return jsonify({
            'status': 'success',
            'data': status
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
