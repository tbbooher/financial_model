"""
Family Office Platform - User Model

Defines the User model with authentication, profile data, and relationships
to accounts, assets, and transactions.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import event

from app import db


class User(db.Model):
    """
    User model representing a family office platform user.

    Attributes:
        id: UUID primary key
        email: Unique email address (used for login)
        password_hash: Bcrypt hashed password
        first_name: User's first name
        last_name: User's last name
        net_worth: Calculated net worth (updated periodically)
        risk_tolerance: Investment risk preference
        is_active: Whether the account is active
        is_verified: Whether email is verified
        mfa_enabled: Whether MFA is enabled
        mfa_secret: MFA secret key (encrypted)
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login: Last login timestamp
    """

    __tablename__ = 'users'

    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    # Financial Profile
    net_worth = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))
    risk_tolerance = db.Column(db.String(20), default='moderate')  # conservative, moderate, aggressive

    # Account Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)

    # Multi-factor Authentication
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.Text)  # Encrypted

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)

    # Relationships
    accounts = db.relationship('Account', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    assets = db.relationship('Asset', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    real_estate = db.relationship('RealEstate', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    agent_tasks = db.relationship('AgentTask', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        """Initialize user with password hashing."""
        password = kwargs.pop('password', None)
        super(User, self).__init__(**kwargs)
        if password:
            self.set_password(password)

    def set_password(self, password: str):
        """
        Hash and set the user's password.

        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Verify a password against the hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        parts = [self.first_name, self.last_name]
        return ' '.join(p for p in parts if p) or self.email

    @property
    def total_assets(self) -> Decimal:
        """Calculate total asset value across all holdings."""
        total = Decimal('0.00')

        # Sum account balances
        for account in self.accounts.filter_by(is_active=True):
            if account.current_balance:
                total += account.current_balance

        # Sum asset values
        for asset in self.assets:
            if asset.current_value:
                total += asset.current_value

        # Sum real estate values
        for property_item in self.real_estate:
            if property_item.current_value:
                total += property_item.current_value

        return total

    @property
    def total_liabilities(self) -> Decimal:
        """Calculate total liabilities (mortgages, loans, etc.)."""
        total = Decimal('0.00')

        # Sum liability accounts
        for account in self.accounts.filter_by(account_type='liability', is_active=True):
            if account.current_balance:
                total += abs(account.current_balance)

        return total

    @property
    def calculated_net_worth(self) -> Decimal:
        """Calculate current net worth (assets - liabilities)."""
        return self.total_assets - self.total_liabilities

    def update_net_worth(self):
        """Update the stored net worth value."""
        self.net_worth = self.calculated_net_worth

    def record_login(self):
        """Record the current time as last login."""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user to dictionary.

        Args:
            include_sensitive: Whether to include sensitive fields

        Returns:
            Dictionary representation of user
        """
        data = {
            'id': str(self.id),
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'net_worth': float(self.net_worth) if self.net_worth else 0.0,
            'risk_tolerance': self.risk_tolerance,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'mfa_enabled': self.mfa_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

        if include_sensitive:
            data['total_assets'] = float(self.total_assets)
            data['total_liabilities'] = float(self.total_liabilities)
            data['calculated_net_worth'] = float(self.calculated_net_worth)

        return data

    def __repr__(self):
        return f'<User {self.email}>'


# Create indexes for performance
db.Index('idx_users_email', User.email)
db.Index('idx_users_created_at', User.created_at)
