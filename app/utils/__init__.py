"""
Family Office Platform - Utility Module

Provides common utilities for encryption, validation, formatting, and custom exceptions.
"""

from app.utils.exceptions import (
    ValidationError,
    CalculationError,
    AuthenticationError,
    AuthorizationError,
    DataIntegrationError,
    AgentError
)
from app.utils.encryption import EncryptionService
from app.utils.validators import (
    validate_email,
    validate_password,
    validate_decimal,
    validate_portfolio_request,
    validate_date_range
)
from app.utils.formatters import (
    format_currency,
    format_percentage,
    format_decimal,
    format_date,
    format_portfolio_summary
)

__all__ = [
    # Exceptions
    'ValidationError',
    'CalculationError',
    'AuthenticationError',
    'AuthorizationError',
    'DataIntegrationError',
    'AgentError',
    # Encryption
    'EncryptionService',
    # Validators
    'validate_email',
    'validate_password',
    'validate_decimal',
    'validate_portfolio_request',
    'validate_date_range',
    # Formatters
    'format_currency',
    'format_percentage',
    'format_decimal',
    'format_date',
    'format_portfolio_summary'
]
