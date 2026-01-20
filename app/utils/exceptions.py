"""
Family Office Platform - Custom Exceptions

Provides custom exception classes for handling various error conditions
throughout the application with proper categorization and error messages.
"""


class FamilyOfficeException(Exception):
    """Base exception class for all Family Office Platform exceptions."""

    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response."""
        return {
            'error': self.code,
            'message': self.message,
            'details': self.details
        }


class ValidationError(FamilyOfficeException):
    """
    Raised when input validation fails.

    Examples:
        - Invalid email format
        - Password doesn't meet requirements
        - Invalid date range
        - Missing required fields
    """

    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, code='VALIDATION_ERROR', details=details)
        self.field = field
        if field:
            self.details['field'] = field


class CalculationError(FamilyOfficeException):
    """
    Raised when a financial calculation fails.

    Examples:
        - Division by zero in returns calculation
        - Insufficient data for beta calculation
        - Invalid input for CAPM analysis
        - Matrix singularity in risk calculations
    """

    def __init__(self, message: str, calculation_type: str = None, details: dict = None):
        super().__init__(message, code='CALCULATION_ERROR', details=details)
        self.calculation_type = calculation_type
        if calculation_type:
            self.details['calculation_type'] = calculation_type


class AuthenticationError(FamilyOfficeException):
    """
    Raised when authentication fails.

    Examples:
        - Invalid credentials
        - Expired token
        - Invalid token format
        - Missing authentication header
    """

    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(message, code='AUTHENTICATION_ERROR', details=details)


class AuthorizationError(FamilyOfficeException):
    """
    Raised when authorization fails.

    Examples:
        - User doesn't have permission to access resource
        - Attempting to access another user's data
        - Role-based access control violation
    """

    def __init__(self, message: str = "Access denied", resource: str = None, details: dict = None):
        super().__init__(message, code='AUTHORIZATION_ERROR', details=details)
        self.resource = resource
        if resource:
            self.details['resource'] = resource


class DataIntegrationError(FamilyOfficeException):
    """
    Raised when external data integration fails.

    Examples:
        - API rate limit exceeded
        - External service unavailable
        - Invalid API response
        - Connection timeout
    """

    def __init__(self, message: str, service: str = None, details: dict = None):
        super().__init__(message, code='DATA_INTEGRATION_ERROR', details=details)
        self.service = service
        if service:
            self.details['service'] = service


class AgentError(FamilyOfficeException):
    """
    Raised when an AI agent encounters an error.

    Examples:
        - Agent analysis timeout
        - Insufficient data for recommendations
        - Agent configuration error
        - Agent task queue full
    """

    def __init__(self, message: str, agent_type: str = None, details: dict = None):
        super().__init__(message, code='AGENT_ERROR', details=details)
        self.agent_type = agent_type
        if agent_type:
            self.details['agent_type'] = agent_type


class DatabaseError(FamilyOfficeException):
    """
    Raised when a database operation fails.

    Examples:
        - Connection failure
        - Query timeout
        - Integrity constraint violation
        - Transaction rollback
    """

    def __init__(self, message: str, operation: str = None, details: dict = None):
        super().__init__(message, code='DATABASE_ERROR', details=details)
        self.operation = operation
        if operation:
            self.details['operation'] = operation


class RateLimitError(FamilyOfficeException):
    """
    Raised when rate limit is exceeded.
    """

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, details: dict = None):
        super().__init__(message, code='RATE_LIMIT_ERROR', details=details)
        self.retry_after = retry_after
        if retry_after:
            self.details['retry_after'] = retry_after


class ConfigurationError(FamilyOfficeException):
    """
    Raised when there's a configuration error.

    Examples:
        - Missing required environment variable
        - Invalid configuration value
        - Incompatible configuration settings
    """

    def __init__(self, message: str, config_key: str = None, details: dict = None):
        super().__init__(message, code='CONFIGURATION_ERROR', details=details)
        self.config_key = config_key
        if config_key:
            self.details['config_key'] = config_key
