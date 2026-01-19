"""
Family Office Platform - Flask Application Factory

This module creates and configures the Flask application with all necessary
extensions, blueprints, and middleware for the family office platform.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery
import redis
import logging
from logging.handlers import RotatingFileHandler
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)
celery = Celery(__name__)

def create_app(config_name='development'):
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    
    # Configure Celery
    configure_celery(app, celery)
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app

def configure_celery(app, celery):
    """Configure Celery for background task processing"""
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_routes={
            'app.tasks.portfolio_tasks.*': {'queue': 'portfolio'},
            'app.tasks.agent_tasks.*': {'queue': 'agents'},
            'app.tasks.data_sync_tasks.*': {'queue': 'data_sync'},
        }
    )
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask

def configure_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Configure file handler
        file_handler = RotatingFileHandler(
            'logs/family_office.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Family Office Platform startup')

def register_blueprints(app):
    """Register all application blueprints"""
    from app.api.auth import auth_bp
    from app.api.portfolio import portfolio_bp
    from app.api.agents import agents_bp
    from app.api.analytics import analytics_bp
    from app.api.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)

def register_error_handlers(app):
    """Register custom error handlers"""
    from flask import jsonify
    from app.utils.exceptions import ValidationError, CalculationError, AuthenticationError
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        response = jsonify({
            'status': 'error',
            'message': str(error),
            'type': 'validation_error'
        })
        response.status_code = 400
        return response
    
    @app.errorhandler(CalculationError)
    def handle_calculation_error(error):
        response = jsonify({
            'status': 'error',
            'message': str(error),
            'type': 'calculation_error'
        })
        response.status_code = 422
        return response
    
    @app.errorhandler(AuthenticationError)
    def handle_auth_error(error):
        response = jsonify({
            'status': 'error',
            'message': str(error),
            'type': 'authentication_error'
        })
        response.status_code = 401
        return response
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found',
            'type': 'not_found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'type': 'internal_error'
        }), 500

def register_cli_commands(app):
    """Register custom CLI commands"""
    @app.cli.command()
    def test():
        """Run the unit tests"""
        import unittest
        tests = unittest.TestLoader().discover('tests')
        unittest.TextTestRunner(verbosity=2).run(tests)
    
    @app.cli.command()
    def init_redis():
        """Initialize Redis connection and test"""
        try:
            r = redis.Redis.from_url(app.config['REDIS_URL'])
            r.ping()
            print("Redis connection successful!")
        except Exception as e:
            print(f"Redis connection failed: {e}")

# Import models to ensure they are registered with SQLAlchemy
from app.models import user, portfolio, transactions, agents