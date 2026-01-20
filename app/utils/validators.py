"""
Family Office Platform - Input Validators

Provides validation functions for user input, financial data, and API requests
to ensure data integrity and security.
"""

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Union

from app.utils.exceptions import ValidationError


# Email validation regex
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Password requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_REQUIRES_UPPERCASE = True
PASSWORD_REQUIRES_LOWERCASE = True
PASSWORD_REQUIRES_DIGIT = True
PASSWORD_REQUIRES_SPECIAL = True
SPECIAL_CHARACTERS = '!@#$%^&*()_+-=[]{}|;:,.<>?'


def validate_email(email: str) -> str:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Normalized (lowercase) email

    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        raise ValidationError("Email is required", field='email')

    email = email.strip().lower()

    if len(email) > 255:
        raise ValidationError("Email address is too long", field='email')

    if not EMAIL_REGEX.match(email):
        raise ValidationError("Invalid email format", field='email')

    return email


def validate_password(password: str, confirm_password: str = None) -> str:
    """
    Validate password meets security requirements.

    Args:
        password: Password to validate
        confirm_password: Optional confirmation password

    Returns:
        Validated password

    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if not password:
        raise ValidationError("Password is required", field='password')

    errors = []

    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")

    if len(password) > PASSWORD_MAX_LENGTH:
        errors.append(f"Password cannot exceed {PASSWORD_MAX_LENGTH} characters")

    if PASSWORD_REQUIRES_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if PASSWORD_REQUIRES_LOWERCASE and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if PASSWORD_REQUIRES_DIGIT and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if PASSWORD_REQUIRES_SPECIAL and not any(c in SPECIAL_CHARACTERS for c in password):
        errors.append(f"Password must contain at least one special character ({SPECIAL_CHARACTERS})")

    if errors:
        raise ValidationError("; ".join(errors), field='password')

    if confirm_password is not None and password != confirm_password:
        raise ValidationError("Passwords do not match", field='confirm_password')

    return password


def validate_decimal(
    value: Any,
    field_name: str = 'value',
    min_value: Decimal = None,
    max_value: Decimal = None,
    precision: int = 6,
    allow_negative: bool = True,
    allow_zero: bool = True
) -> Decimal:
    """
    Validate and convert a value to Decimal.

    Args:
        value: Value to validate (string, int, float, or Decimal)
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        precision: Number of decimal places to allow
        allow_negative: Whether negative values are allowed
        allow_zero: Whether zero is allowed

    Returns:
        Validated Decimal value

    Raises:
        ValidationError: If value is invalid
    """
    if value is None:
        raise ValidationError(f"{field_name} is required", field=field_name)

    try:
        if isinstance(value, float):
            # Convert float to string first to avoid precision issues
            decimal_value = Decimal(str(value))
        else:
            decimal_value = Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"Invalid decimal value for {field_name}", field=field_name)

    # Check for special values
    if decimal_value.is_nan() or decimal_value.is_infinite():
        raise ValidationError(f"{field_name} must be a finite number", field=field_name)

    # Check negative
    if not allow_negative and decimal_value < 0:
        raise ValidationError(f"{field_name} cannot be negative", field=field_name)

    # Check zero
    if not allow_zero and decimal_value == 0:
        raise ValidationError(f"{field_name} cannot be zero", field=field_name)

    # Check min/max
    if min_value is not None and decimal_value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}", field=field_name)

    if max_value is not None and decimal_value > max_value:
        raise ValidationError(f"{field_name} must not exceed {max_value}", field=field_name)

    # Round to precision
    quantize_str = '0.' + '0' * precision if precision > 0 else '0'
    return decimal_value.quantize(Decimal(quantize_str))


def validate_portfolio_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate portfolio API request data.

    Args:
        data: Request data dictionary

    Returns:
        Validated and cleaned data

    Raises:
        ValidationError: If request data is invalid
    """
    if not data:
        raise ValidationError("Request body is required")

    validated = {}

    # Validate period if present
    if 'period' in data:
        valid_periods = ['1D', '1W', '1M', '3M', '6M', '1Y', '2Y', '5Y', 'YTD', 'ALL']
        period = data['period'].upper()
        if period not in valid_periods:
            raise ValidationError(
                f"Invalid period. Must be one of: {', '.join(valid_periods)}",
                field='period'
            )
        validated['period'] = period

    # Validate asset_type if present
    if 'asset_type' in data:
        valid_types = ['stock', 'bond', 'etf', 'mutual_fund', 'real_estate',
                       'startup_equity', 'cash', 'crypto', 'other']
        asset_type = data['asset_type'].lower()
        if asset_type not in valid_types:
            raise ValidationError(
                f"Invalid asset type. Must be one of: {', '.join(valid_types)}",
                field='asset_type'
            )
        validated['asset_type'] = asset_type

    # Validate symbol if present
    if 'symbol' in data:
        symbol = data['symbol'].upper().strip()
        if not symbol or len(symbol) > 20:
            raise ValidationError("Invalid symbol", field='symbol')
        validated['symbol'] = symbol

    # Validate quantity if present
    if 'quantity' in data:
        validated['quantity'] = validate_decimal(
            data['quantity'],
            field_name='quantity',
            allow_negative=False,
            allow_zero=False
        )

    # Validate value/amount if present
    if 'value' in data:
        validated['value'] = validate_decimal(
            data['value'],
            field_name='value',
            allow_negative=False
        )

    if 'amount' in data:
        validated['amount'] = validate_decimal(
            data['amount'],
            field_name='amount'
        )

    return validated


def validate_date_range(
    start_date: Union[str, date, datetime],
    end_date: Union[str, date, datetime],
    max_days: int = None
) -> Tuple[date, date]:
    """
    Validate a date range.

    Args:
        start_date: Start date (string, date, or datetime)
        end_date: End date (string, date, or datetime)
        max_days: Maximum allowed days in range

    Returns:
        Tuple of (start_date, end_date) as date objects

    Raises:
        ValidationError: If date range is invalid
    """
    # Parse start date
    if isinstance(start_date, str):
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Invalid start date format. Use YYYY-MM-DD", field='start_date')
    elif isinstance(start_date, datetime):
        start = start_date.date()
    elif isinstance(start_date, date):
        start = start_date
    else:
        raise ValidationError("Invalid start date type", field='start_date')

    # Parse end date
    if isinstance(end_date, str):
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Invalid end date format. Use YYYY-MM-DD", field='end_date')
    elif isinstance(end_date, datetime):
        end = end_date.date()
    elif isinstance(end_date, date):
        end = end_date
    else:
        raise ValidationError("Invalid end date type", field='end_date')

    # Validate range
    if start > end:
        raise ValidationError("Start date must be before or equal to end date", field='start_date')

    if max_days is not None:
        delta = (end - start).days
        if delta > max_days:
            raise ValidationError(f"Date range cannot exceed {max_days} days", field='end_date')

    return start, end


def validate_risk_tolerance(value: str) -> str:
    """
    Validate risk tolerance level.

    Args:
        value: Risk tolerance level

    Returns:
        Validated risk tolerance

    Raises:
        ValidationError: If invalid
    """
    valid_values = ['conservative', 'moderate', 'aggressive']
    if not value:
        raise ValidationError("Risk tolerance is required", field='risk_tolerance')

    value = value.lower().strip()
    if value not in valid_values:
        raise ValidationError(
            f"Invalid risk tolerance. Must be one of: {', '.join(valid_values)}",
            field='risk_tolerance'
        )

    return value


def validate_uuid(value: str, field_name: str = 'id') -> str:
    """
    Validate UUID format.

    Args:
        value: UUID string to validate
        field_name: Field name for error message

    Returns:
        Validated UUID string

    Raises:
        ValidationError: If invalid UUID
    """
    import uuid

    if not value:
        raise ValidationError(f"{field_name} is required", field=field_name)

    try:
        uuid_obj = uuid.UUID(str(value))
        return str(uuid_obj)
    except (ValueError, AttributeError):
        raise ValidationError(f"Invalid {field_name} format", field=field_name)


def sanitize_string(value: str, max_length: int = None, allow_html: bool = False) -> str:
    """
    Sanitize a string input.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags

    Returns:
        Sanitized string
    """
    if not value:
        return value

    # Strip whitespace
    value = value.strip()

    # Remove HTML if not allowed
    if not allow_html:
        value = re.sub(r'<[^>]+>', '', value)

    # Truncate if needed
    if max_length and len(value) > max_length:
        value = value[:max_length]

    return value


def sanitize_input(value: str) -> str:
    """
    Sanitize user input to prevent XSS and SQL injection.

    Args:
        value: User input to sanitize

    Returns:
        Sanitized string safe for storage and display
    """
    if not value:
        return value

    # Remove HTML tags (XSS prevention)
    value = re.sub(r'<[^>]+>', '', value)

    # Remove potential SQL injection characters
    # Replace dangerous characters with safe alternatives
    dangerous_chars = {
        "'": "''",  # Escape single quotes
        '"': '""',  # Escape double quotes
        ';': '',    # Remove semicolons
        '--': '',   # Remove SQL comments
        '/*': '',   # Remove block comment start
        '*/': '',   # Remove block comment end
    }

    for char, replacement in dangerous_chars.items():
        value = value.replace(char, replacement)

    return value.strip()
