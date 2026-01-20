"""
Family Office Platform - API Module

REST API blueprints for authentication, portfolio management,
agent interactions, analytics, and administration.
"""

from app.api.auth import auth_bp
from app.api.portfolio import portfolio_bp
from app.api.agents import agents_bp
from app.api.analytics import analytics_bp
from app.api.admin import admin_bp

__all__ = [
    'auth_bp',
    'portfolio_bp',
    'agents_bp',
    'analytics_bp',
    'admin_bp'
]
