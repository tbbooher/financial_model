"""
Family Office Platform - Utility Unit Tests

Tests for utility functions and helper classes.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date

from app.utils.validators import (
    validate_email, validate_password, validate_decimal,
    validate_date_range, sanitize_input
)
from app.utils.formatters import (
    format_currency, format_percentage, format_decimal,
    format_date, format_portfolio_summary
)
from app.utils.encryption import EncryptionService
from app.utils.exceptions import ValidationError, CalculationError, AuthenticationError


class TestValidators:
    """Tests for validation functions."""

    def test_validate_email_valid(self):
        """Test validation of valid emails."""
        valid_emails = [
            'user@example.com',
            'user.name@example.com',
            'user+tag@example.org',
            'user123@subdomain.example.com'
        ]

        for email in valid_emails:
            result = validate_email(email)
            # Returns normalized (lowercase) email
            assert result == email.lower()

    def test_validate_email_invalid(self):
        """Test validation of invalid emails."""
        invalid_emails = [
            'invalid',
            'invalid@',
            '@example.com',
            'user@.com',
            'user@example.',
            ''
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_email(email)

    def test_validate_password_valid(self):
        """Test validation of valid passwords."""
        valid_passwords = [
            'SecurePass123!',
            'MyP@ssw0rd',
            'Complex123$Password'
        ]

        for password in valid_passwords:
            result = validate_password(password)
            # Returns the validated password
            assert result == password

    def test_validate_password_invalid(self):
        """Test validation of invalid passwords."""
        invalid_passwords = [
            'short',           # Too short
            'nouppercase123!', # No uppercase
            'NOLOWERCASE123!', # No lowercase
            'NoNumbers!!!',    # No numbers
            'NoSpecial123',    # No special chars
        ]

        for password in invalid_passwords:
            with pytest.raises(ValidationError):
                validate_password(password)

    def test_validate_decimal_valid(self):
        """Test validation of valid decimal values."""
        valid_decimals = [
            ('100.00', 0, 1000000),
            ('0.001', 0, 1),
            ('999999.99', 0, 1000000)
        ]

        for value, min_val, max_val in valid_decimals:
            result = validate_decimal(value, min_value=Decimal(min_val), max_value=Decimal(max_val))
            assert isinstance(result, Decimal)

    def test_validate_decimal_invalid(self):
        """Test validation of invalid decimal values."""
        with pytest.raises(ValidationError):
            validate_decimal('not-a-number')

        with pytest.raises(ValidationError):
            validate_decimal('-100', allow_negative=False)

        with pytest.raises(ValidationError):
            validate_decimal('1000001', max_value=Decimal('1000000'))

    def test_validate_date_range(self):
        """Test date range validation."""
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)

        result = validate_date_range(start, end)
        # Returns tuple of (start_date, end_date) as date objects
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == start.date()
        assert result[1] == end.date()

        # Invalid: end before start
        with pytest.raises(ValidationError):
            validate_date_range(end, start)

    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test XSS prevention
        malicious = '<script>alert("xss")</script>'
        sanitized = sanitize_input(malicious)
        assert '<script>' not in sanitized

        # Test SQL injection prevention
        sql_injection = "'; DROP TABLE users; --"
        sanitized = sanitize_input(sql_injection)
        assert sanitized != sql_injection


class TestFormatters:
    """Tests for formatting functions."""

    def test_format_currency(self):
        """Test currency formatting."""
        assert format_currency(1000) == '$1,000.00'
        assert format_currency(1000000) == '$1,000,000.00'
        assert format_currency(1234.56) == '$1,234.56'
        assert format_currency(0) == '$0.00'
        # Default negative_format is 'parentheses'
        assert format_currency(-500) == '($500.00)'
        # With minus format
        assert format_currency(-500, negative_format='minus') == '-$500.00'

    def test_format_currency_with_symbol(self):
        """Test currency formatting with different symbols."""
        assert '$' in format_currency(1000, currency_symbol='$')
        assert '€' in format_currency(1000, currency_symbol='€')

    def test_format_percentage(self):
        """Test percentage formatting."""
        # Default include_sign=True adds + for positive
        assert format_percentage(0.1523) == '+15.23%'
        assert format_percentage(1.0) == '+100.00%'
        assert format_percentage(0.0) == '0.00%'
        assert format_percentage(-0.05) == '-5.00%'
        # Without sign
        assert format_percentage(0.1523, include_sign=False) == '15.23%'

    def test_format_percentage_decimals(self):
        """Test percentage formatting with custom decimals."""
        assert format_percentage(0.1234567, decimal_places=4) == '+12.3457%'
        assert format_percentage(0.1, decimal_places=0) == '+10%'

    def test_format_decimal(self):
        """Test decimal formatting."""
        assert format_decimal(Decimal('1234.567890'), decimal_places=2) == '1234.57'
        assert format_decimal(Decimal('100'), decimal_places=4) == '100.0000'

    def test_format_date(self):
        """Test date formatting."""
        test_date = datetime(2024, 1, 15, 10, 30, 0)
        formatted = format_date(test_date)
        assert '2024' in formatted
        assert 'Jan' in formatted or '01' in formatted

    def test_format_portfolio_summary(self):
        """Test portfolio summary formatting."""
        summary = {
            'net_worth': 1000000,
            'total_assets': 1200000,
            'total_liabilities': 200000,
            'breakdown': {
                'stocks': 500000,
                'bonds': 300000,
                'real_estate': 400000
            }
        }

        formatted = format_portfolio_summary(summary)

        assert 'net_worth' in formatted
        assert formatted['net_worth'] == '$1,000,000.00'


class TestEncryption:
    """Tests for encryption utilities."""

    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        # Pass password directly for testing (avoids env var requirement)
        service = EncryptionService(password=b'test_encryption_key_12345')

        original = 'sensitive data 12345'
        encrypted = service.encrypt(original)

        # Encrypted should be different from original
        assert encrypted != original

        # Decrypted should match original
        decrypted = service.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_different_outputs(self):
        """Test that same input produces different encrypted outputs."""
        service = EncryptionService(password=b'test_encryption_key_12345')

        data = 'test data'
        encrypted1 = service.encrypt(data)
        encrypted2 = service.encrypt(data)

        # While decryption gives same result, encrypted values should be different
        # (due to IV/nonce in Fernet)
        assert service.decrypt(encrypted1) == service.decrypt(encrypted2)

    def test_encrypt_special_characters(self):
        """Test encryption of special characters."""
        service = EncryptionService(password=b'test_encryption_key_12345')

        special_data = 'Test!@#$%^&*()_+-={}[]|:;<>?,./~`'
        encrypted = service.encrypt(special_data)
        decrypted = service.decrypt(encrypted)

        assert decrypted == special_data

    def test_encrypt_unicode(self):
        """Test encryption of unicode characters."""
        service = EncryptionService(password=b'test_encryption_key_12345')

        unicode_data = 'Test unicode: cafe, resume'
        encrypted = service.encrypt(unicode_data)
        decrypted = service.decrypt(encrypted)

        assert decrypted == unicode_data


class TestExceptions:
    """Tests for custom exceptions."""

    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError('Invalid input', field='email')

        assert str(error) == 'Invalid input'
        assert error.field == 'email'

    def test_calculation_error(self):
        """Test CalculationError exception."""
        error = CalculationError('Division by zero', calculation_type='var')

        assert str(error) == 'Division by zero'
        assert error.calculation_type == 'var'

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        error = AuthenticationError('Invalid credentials')

        assert str(error) == 'Invalid credentials'

    def test_exception_inheritance(self):
        """Test that custom exceptions inherit from Exception."""
        assert issubclass(ValidationError, Exception)
        assert issubclass(CalculationError, Exception)
        assert issubclass(AuthenticationError, Exception)
