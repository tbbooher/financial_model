"""
Family Office Platform - Configuration Management

This module contains configuration classes for different environments
(development, testing, production) with security and performance settings.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class with common settings"""
    
    # Flask Core Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://family_office:password@localhost:5432/family_office_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 30)))
    JWT_ALGORITHM = 'HS256'
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = False  # Set to True in production with HTTPS
    JWT_COOKIE_CSRF_PROTECT = False  # Simplified for development
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token_cookie'
    
    # Security Settings
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', 12))
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or 'encryption-key-change-in-production'
    
    # CORS Settings
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000']
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/1'
    RATELIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '100/hour')
    
    # External API Keys
    ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
    IEX_CLOUD_API_KEY = os.environ.get('IEX_CLOUD_API_KEY')
    PLAID_CLIENT_ID = os.environ.get('PLAID_CLIENT_ID')
    PLAID_SECRET = os.environ.get('PLAID_SECRET')
    PLAID_ENV = os.environ.get('PLAID_ENV', 'sandbox')
    ZILLOW_API_KEY = os.environ.get('ZILLOW_API_KEY')
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Portfolio Configuration
    DEFAULT_RISK_FREE_RATE = float(os.environ.get('DEFAULT_RISK_FREE_RATE', 0.02))
    DEFAULT_MARKET_SYMBOL = os.environ.get('DEFAULT_MARKET_SYMBOL', '^GSPC')
    PORTFOLIO_UPDATE_INTERVAL = int(os.environ.get('PORTFOLIO_UPDATE_INTERVAL', 300))
    
    # Agent Configuration
    AGENT_CONFIDENCE_THRESHOLD = float(os.environ.get('AGENT_CONFIDENCE_THRESHOLD', 0.7))
    MAX_AGENT_PROCESSING_TIME = int(os.environ.get('MAX_AGENT_PROCESSING_TIME', 30))
    AGENT_RETRY_ATTEMPTS = int(os.environ.get('AGENT_RETRY_ATTEMPTS', 3))
    
    # Cache Configuration
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/2'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Monitoring & Logging
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        pass

class DevelopmentConfig(Config):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Relaxed security for development
    WTF_CSRF_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Longer tokens for dev
    
    # Development database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://family_office:password@localhost:5432/family_office_dev'
    
    # Development logging
    LOG_LEVEL = 'DEBUG'
    
    # Development CORS - allow all origins
    CORS_ORIGINS = ['*']

class TestingConfig(Config):
    """Testing environment configuration"""

    TESTING = True
    DEBUG = False

    # In-memory SQLite database for testing (no external DB required)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_TEST_URL') or 'sqlite:///:memory:'

    # SQLite doesn't need pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 4

    # Short token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=1)

    # Test Redis database (use memory if Redis unavailable)
    REDIS_URL = 'redis://localhost:6379/15'
    CELERY_BROKER_URL = 'redis://localhost:6379/15'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/15'

    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False

    # Set encryption key for testing
    ENCRYPTION_KEY = 'test-encryption-key-for-testing-only'

class ProductionConfig(Config):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Strict CORS in production
    CORS_ORIGINS = [
        'https://familyoffice.yourdomain.com',
        'https://app.familyoffice.yourdomain.com'
    ]
    
    # Production database with SSL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'max_overflow': 40,
        'connect_args': {
            'sslmode': 'require',
            'connect_timeout': 10
        }
    }
    
    # Enhanced security
    BCRYPT_LOG_ROUNDS = 15
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Production rate limiting
    RATELIMIT_DEFAULT = '50/hour'
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization"""
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class DockerConfig(ProductionConfig):
    """Docker container configuration"""
    
    @classmethod
    def init_app(cls, app):
        """Docker-specific initialization"""
        ProductionConfig.init_app(app)
        
        # Log to stdout in Docker
        import logging
        import sys
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}