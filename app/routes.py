"""
Family Office Platform - Web Routes

Flask routes for rendering HTML templates and serving the frontend.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from functools import wraps

main_bp = Blueprint('main', __name__)


def login_required_web(f):
    """Decorator for web routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request(locations=['cookies', 'headers'])
            return f(*args, **kwargs)
        except Exception:
            return redirect(url_for('main.login'))
    return decorated_function


def get_current_user():
    """Get current user from JWT token."""
    try:
        verify_jwt_in_request(locations=['cookies', 'headers'], optional=True)
        user_id = get_jwt_identity()
        if user_id:
            from app.models import User
            from app import db
            import uuid
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            return db.session.get(User, user_uuid)
    except Exception:
        pass
    return None


@main_bp.context_processor
def inject_user():
    """Inject current user into all templates."""
    return {'current_user': get_current_user()}


# Public Routes
@main_bp.route('/')
def index():
    """Landing page."""
    user = get_current_user()
    if user:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        # Handle form submission - redirect to API
        return redirect(url_for('main.dashboard'))
    return render_template('pages/login.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page."""
    if request.method == 'POST':
        # Handle form submission - redirect to API
        return redirect(url_for('main.login'))
    return render_template('pages/register.html')


@main_bp.route('/logout')
def logout():
    """Logout user - renders page that clears localStorage and cookies."""
    return render_template('pages/logout.html')


# Protected Routes
@main_bp.route('/dashboard')
@login_required_web
def dashboard():
    """Main dashboard page."""
    return render_template('pages/dashboard.html')


@main_bp.route('/portfolio')
@login_required_web
def portfolio():
    """Portfolio management page."""
    return render_template('pages/portfolio.html')


@main_bp.route('/analytics')
@login_required_web
def analytics():
    """Financial analytics page."""
    return render_template('pages/analytics.html')


@main_bp.route('/agents')
@login_required_web
def agents():
    """AI agents page."""
    return render_template('pages/agents.html')


@main_bp.route('/profile')
@login_required_web
def profile():
    """User profile page."""
    return render_template('pages/profile.html')


@main_bp.route('/settings')
@login_required_web
def settings():
    """User settings page."""
    return render_template('pages/settings.html')


# Error Handlers
@main_bp.app_errorhandler(404)
def page_not_found(e):
    """404 error handler."""
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(500)
def internal_server_error(e):
    """500 error handler."""
    return render_template('errors/500.html'), 500
