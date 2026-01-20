"""
Family Office Platform - Authentication API

REST endpoints for user authentication, registration, and token management.
"""

from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt,
    create_access_token, create_refresh_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies
)
from datetime import datetime

from app.services.auth_service import AuthService
from app.utils.exceptions import AuthenticationError, ValidationError

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

auth_service = AuthService()


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.

    Request Body:
        email: User email
        password: User password
        first_name: Optional first name
        last_name: Optional last name
        risk_tolerance: Optional risk tolerance (conservative, moderate, aggressive)

    Returns:
        User info and JWT tokens
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request body is required'
            }), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400

        user = auth_service.create_user(
            email=email,
            password=password,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            risk_tolerance=data.get('risk_tolerance', 'moderate')
        )

        tokens = auth_service.generate_tokens(user)

        # Create response with JWT cookies for web auth
        response = make_response(jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'user': user.to_dict(),
                'tokens': tokens
            }
        }), 201)

        # Set JWT cookies for server-side authentication
        set_access_cookies(response, tokens['access_token'])
        set_refresh_cookies(response, tokens['refresh_token'])

        return response

    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'field': e.field if hasattr(e, 'field') else None
        }), 400
    except AuthenticationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 409
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Registration failed'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT tokens.

    Request Body:
        email: User email
        password: User password

    Returns:
        User info and JWT tokens
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request body is required'
            }), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400

        user, tokens = auth_service.authenticate(email, password)

        # Create response with JWT cookies for web auth
        response = make_response(jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'user': user.to_dict(),
                'tokens': tokens
            }
        }), 200)

        # Set JWT cookies for server-side authentication
        set_access_cookies(response, tokens['access_token'])
        set_refresh_cookies(response, tokens['refresh_token'])

        return response

    except AuthenticationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 401
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': 'Login failed',
            'debug': str(e) if current_app.debug else None
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token.

    Headers:
        Authorization: Bearer <refresh_token>

    Returns:
        New access token
    """
    try:
        user_id = get_jwt_identity()
        tokens = auth_service.refresh_access_token(user_id)

        return jsonify({
            'status': 'success',
            'data': tokens
        }), 200

    except AuthenticationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 401
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Token refresh failed'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required(optional=True)
def logout():
    """
    Logout user (invalidate token on client side and clear cookies).

    Note: For full token invalidation, implement token blacklist.

    Returns:
        Success message
    """
    # Create response and clear JWT cookies
    response = make_response(jsonify({
        'status': 'success',
        'message': 'Logout successful'
    }), 200)

    unset_jwt_cookies(response)

    return response


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user info.

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        User info
    """
    try:
        user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(user_id)

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
            'message': 'Failed to get user info'
        }), 500


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """
    Update current user profile.

    Request Body:
        first_name: Optional new first name
        last_name: Optional new last name
        risk_tolerance: Optional new risk tolerance

    Returns:
        Updated user info
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        user = auth_service.update_user_profile(
            user_id=user_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            risk_tolerance=data.get('risk_tolerance')
        )

        return jsonify({
            'status': 'success',
            'message': 'Profile updated',
            'data': user.to_dict()
        }), 200

    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except AuthenticationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to update profile'
        }), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password.

    Request Body:
        current_password: Current password
        new_password: New password

    Returns:
        Success message
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request body is required'
            }), 400

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({
                'status': 'error',
                'message': 'Current and new passwords are required'
            }), 400

        auth_service.change_password(user_id, current_password, new_password)

        return jsonify({
            'status': 'success',
            'message': 'Password changed successfully'
        }), 200

    except AuthenticationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 401
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to change password'
        }), 500
