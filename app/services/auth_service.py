"""
Family Office Platform - Authentication Service

Provides user authentication, registration, and JWT token management.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Tuple, Dict, Any

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from app import db
from app.models import User
from app.utils.validators import validate_email, validate_password, validate_risk_tolerance
from app.utils.exceptions import AuthenticationError, ValidationError


class AuthService:
    """Service for handling user authentication and authorization."""

    def __init__(self):
        """Initialize auth service."""
        pass

    def create_user(
        self,
        email: str,
        password: str,
        first_name: str = None,
        last_name: str = None,
        net_worth: Decimal = None,
        risk_tolerance: str = 'moderate'
    ) -> User:
        """
        Create a new user account.

        Args:
            email: User email address
            password: User password
            first_name: Optional first name
            last_name: Optional last name
            net_worth: Optional initial net worth
            risk_tolerance: Investment risk tolerance

        Returns:
            Created User instance

        Raises:
            ValidationError: If input validation fails
            AuthenticationError: If user already exists
        """
        # Validate inputs
        email = validate_email(email)
        password = validate_password(password)
        risk_tolerance = validate_risk_tolerance(risk_tolerance)

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise AuthenticationError("User with this email already exists")

        # Create user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            net_worth=net_worth or Decimal('0.00'),
            risk_tolerance=risk_tolerance
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user

    def authenticate(self, email: str, password: str) -> Tuple[User, Dict[str, str]]:
        """
        Authenticate user and return JWT tokens.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (User, tokens dict)

        Raises:
            AuthenticationError: If authentication fails
        """
        # Validate email format
        try:
            email = validate_email(email)
        except ValidationError:
            raise AuthenticationError("Invalid email or password")

        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            raise AuthenticationError("Invalid email or password")

        # Check if account is active
        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        # Verify password
        if not user.check_password(password):
            raise AuthenticationError("Invalid email or password")

        # Record login
        user.record_login()

        # Generate tokens
        tokens = self.generate_tokens(user)

        return user, tokens

    def generate_tokens(self, user: User) -> Dict[str, str]:
        """
        Generate JWT access and refresh tokens for user.

        Args:
            user: User instance

        Returns:
            Dictionary with access_token and refresh_token
        """
        # Create identity payload
        identity = str(user.id)

        # Additional claims
        additional_claims = {
            'email': user.email,
            'risk_tolerance': user.risk_tolerance
        }

        # Generate tokens
        access_token = create_access_token(
            identity=identity,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=identity,
            additional_claims=additional_claims
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }

    def refresh_access_token(self, user_id: str) -> Dict[str, str]:
        """
        Generate a new access token.

        Args:
            user_id: User ID from refresh token

        Returns:
            Dictionary with new access_token

        Raises:
            AuthenticationError: If user not found or inactive
        """
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        user = db.session.get(User, user_uuid)
        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        additional_claims = {
            'email': user.email,
            'risk_tolerance': user.risk_tolerance
        }

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        return {
            'access_token': access_token,
            'token_type': 'Bearer'
        }

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            AuthenticationError: If current password is wrong
            ValidationError: If new password doesn't meet requirements
        """
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        user = db.session.get(User, user_uuid)
        if not user:
            raise AuthenticationError("User not found")

        if not user.check_password(current_password):
            raise AuthenticationError("Current password is incorrect")

        # Validate new password
        new_password = validate_password(new_password)

        user.set_password(new_password)
        db.session.commit()

        return True

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User instance or None
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            return db.session.get(User, user_uuid)
        except (ValueError, TypeError):
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User instance or None
        """
        return User.query.filter_by(email=email.lower()).first()

    def update_user_profile(
        self,
        user_id: str,
        first_name: str = None,
        last_name: str = None,
        risk_tolerance: str = None
    ) -> User:
        """
        Update user profile.

        Args:
            user_id: User ID
            first_name: Optional new first name
            last_name: Optional new last name
            risk_tolerance: Optional new risk tolerance

        Returns:
            Updated User instance

        Raises:
            AuthenticationError: If user not found
        """
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        user = db.session.get(User, user_uuid)
        if not user:
            raise AuthenticationError("User not found")

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if risk_tolerance is not None:
            user.risk_tolerance = validate_risk_tolerance(risk_tolerance)

        db.session.commit()
        return user

    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            True if deactivated successfully
        """
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        user = db.session.get(User, user_uuid)
        if not user:
            raise AuthenticationError("User not found")

        user.is_active = False
        db.session.commit()
        return True

    def reactivate_user(self, user_id: str) -> bool:
        """
        Reactivate a user account.

        Args:
            user_id: User ID

        Returns:
            True if reactivated successfully
        """
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        user = db.session.get(User, user_uuid)
        if not user:
            raise AuthenticationError("User not found")

        user.is_active = True
        db.session.commit()
        return True
