"""
Family Office Platform - Portfolio Models

Defines models for financial accounts, assets, and real estate holdings.
"""

import uuid
from datetime import datetime, date, timezone
from decimal import Decimal

from sqlalchemy.dialects.postgresql import UUID

from app import db


class Account(db.Model):
    """
    Financial account model (brokerage, retirement, bank, etc.).

    Represents connected financial accounts for tracking balances
    and transactions.
    """

    __tablename__ = 'accounts'

    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)

    # Account Details
    account_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: brokerage, retirement, 529, bank, credit_card, loan, liability
    account_name = db.Column(db.String(255))
    institution = db.Column(db.String(255))
    account_number_encrypted = db.Column(db.Text)  # Encrypted

    # Financial Data
    current_balance = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))

    # Sync Status
    last_synced = db.Column(db.DateTime)
    sync_status = db.Column(db.String(50), default='pending')  # pending, synced, error
    sync_error = db.Column(db.Text)

    # Plaid Integration
    plaid_access_token = db.Column(db.Text)  # Encrypted
    plaid_item_id = db.Column(db.String(255))
    plaid_account_id = db.Column(db.String(255))

    # Status
    is_active = db.Column(db.Boolean, default=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships - explicitly specify foreign_keys since Transaction has both account_id and related_account_id
    transactions = db.relationship(
        'Transaction',
        foreign_keys='Transaction.account_id',
        backref='account',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def masked_account_number(self) -> str:
        """Get masked account number for display."""
        if not self.account_number_encrypted:
            return None
        # In production, decrypt then mask
        return '****' + 'XXXX'

    @property
    def is_liability(self) -> bool:
        """Check if this is a liability account."""
        return self.account_type in ['loan', 'credit_card', 'mortgage', 'liability']

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'account_type': self.account_type,
            'account_name': self.account_name,
            'institution': self.institution,
            'current_balance': float(self.current_balance) if self.current_balance else 0.0,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'sync_status': self.sync_status,
            'is_active': self.is_active,
            'is_liability': self.is_liability,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Account {self.account_name} ({self.account_type})>'


class Asset(db.Model):
    """
    Investment asset model (stocks, bonds, ETFs, etc.).

    Represents individual investment holdings with cost basis
    and current valuation.
    """

    __tablename__ = 'assets'

    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey('accounts.id'), nullable=True)

    # Asset Details
    asset_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: stock, bond, etf, mutual_fund, startup_equity, crypto, cash, other
    symbol = db.Column(db.String(20), index=True)
    name = db.Column(db.String(255))

    # Holdings
    quantity = db.Column(db.Numeric(15, 6), default=Decimal('0.000000'))
    cost_basis = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))
    current_price = db.Column(db.Numeric(15, 6))
    current_value = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))

    # Market Data
    sector = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    exchange = db.Column(db.String(50))

    # Performance Metrics (cached)
    beta = db.Column(db.Numeric(10, 6))
    alpha = db.Column(db.Numeric(10, 6))
    return_1d = db.Column(db.Numeric(10, 6))
    return_1w = db.Column(db.Numeric(10, 6))
    return_1m = db.Column(db.Numeric(10, 6))
    return_3m = db.Column(db.Numeric(10, 6))
    return_1y = db.Column(db.Numeric(10, 6))
    return_ytd = db.Column(db.Numeric(10, 6))

    # Timestamps
    purchase_date = db.Column(db.Date)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def unrealized_gain_loss(self) -> Decimal:
        """Calculate unrealized gain/loss."""
        if self.current_value and self.cost_basis:
            return self.current_value - self.cost_basis
        return Decimal('0.00')

    @property
    def unrealized_gain_loss_percent(self) -> Decimal:
        """Calculate unrealized gain/loss percentage."""
        if self.cost_basis and self.cost_basis != 0:
            return (self.unrealized_gain_loss / self.cost_basis) * 100
        return Decimal('0.00')

    @property
    def return_percentage(self) -> Decimal:
        """Calculate total return percentage."""
        if self.cost_basis and self.cost_basis != 0:
            return ((self.current_value - self.cost_basis) / self.cost_basis) * 100
        return Decimal('0.00')

    def update_value(self, price: Decimal):
        """Update current value based on price."""
        self.current_price = price
        self.current_value = self.quantity * price
        self.last_updated = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'account_id': str(self.account_id) if self.account_id else None,
            'asset_type': self.asset_type,
            'symbol': self.symbol,
            'name': self.name,
            'quantity': float(self.quantity) if self.quantity else 0.0,
            'cost_basis': float(self.cost_basis) if self.cost_basis else 0.0,
            'current_price': float(self.current_price) if self.current_price else 0.0,
            'current_value': float(self.current_value) if self.current_value else 0.0,
            'unrealized_gain_loss': float(self.unrealized_gain_loss),
            'unrealized_gain_loss_percent': float(self.unrealized_gain_loss_percent),
            'return_percentage': float(self.return_percentage),
            'beta': float(self.beta) if self.beta else None,
            'sector': self.sector,
            'industry': self.industry,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    def __repr__(self):
        return f'<Asset {self.symbol or self.name} ({self.asset_type})>'


class RealEstate(db.Model):
    """
    Real estate property model.

    Represents real estate holdings including primary residence
    and rental properties.
    """

    __tablename__ = 'real_estate'

    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Key
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)

    # Property Details
    property_type = db.Column(db.String(50), nullable=False)  # primary, rental, commercial, land
    property_name = db.Column(db.String(255))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='USA')

    # Valuation
    purchase_price = db.Column(db.Numeric(15, 2))
    current_value = db.Column(db.Numeric(15, 2))
    valuation_source = db.Column(db.String(100))  # zillow, appraisal, manual

    # Mortgage/Financing
    mortgage_balance = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))
    mortgage_rate = db.Column(db.Numeric(5, 4))  # e.g., 0.0425 for 4.25%
    mortgage_payment = db.Column(db.Numeric(10, 2))

    # Income/Expenses (for rental properties)
    monthly_income = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))
    monthly_expenses = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))
    # Breakdown
    property_tax_annual = db.Column(db.Numeric(10, 2))
    insurance_annual = db.Column(db.Numeric(10, 2))
    hoa_monthly = db.Column(db.Numeric(10, 2))
    maintenance_annual = db.Column(db.Numeric(10, 2))

    # Property Attributes
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Numeric(3, 1))
    square_feet = db.Column(db.Integer)
    lot_size = db.Column(db.Numeric(10, 2))  # acres or sq ft
    year_built = db.Column(db.Integer)

    # Dates
    purchase_date = db.Column(db.Date)
    last_valuation_date = db.Column(db.Date)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def equity(self) -> Decimal:
        """Calculate equity (value - mortgage)."""
        value = self.current_value or Decimal('0.00')
        mortgage = self.mortgage_balance or Decimal('0.00')
        return value - mortgage

    @property
    def net_monthly_income(self) -> Decimal:
        """Calculate net monthly income from property."""
        income = self.monthly_income or Decimal('0.00')
        expenses = self.monthly_expenses or Decimal('0.00')
        mortgage = self.mortgage_payment or Decimal('0.00')
        return income - expenses - mortgage

    @property
    def annual_roi(self) -> Decimal:
        """Calculate annual ROI based on rental income."""
        if not self.purchase_price or self.purchase_price == 0:
            return Decimal('0.00')

        annual_net_income = self.net_monthly_income * 12
        return (annual_net_income / self.purchase_price) * 100

    @property
    def cap_rate(self) -> Decimal:
        """Calculate capitalization rate (NOI / Property Value)."""
        if not self.current_value or self.current_value == 0:
            return Decimal('0.00')

        noi = (self.monthly_income or Decimal('0.00')) * 12
        noi -= (self.monthly_expenses or Decimal('0.00')) * 12
        return (noi / self.current_value) * 100

    @property
    def appreciation(self) -> Decimal:
        """Calculate total appreciation since purchase."""
        if self.purchase_price and self.current_value:
            return self.current_value - self.purchase_price
        return Decimal('0.00')

    @property
    def appreciation_percent(self) -> Decimal:
        """Calculate appreciation percentage."""
        if self.purchase_price and self.purchase_price != 0:
            return (self.appreciation / self.purchase_price) * 100
        return Decimal('0.00')

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'property_type': self.property_type,
            'property_name': self.property_name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'purchase_price': float(self.purchase_price) if self.purchase_price else 0.0,
            'current_value': float(self.current_value) if self.current_value else 0.0,
            'mortgage_balance': float(self.mortgage_balance) if self.mortgage_balance else 0.0,
            'equity': float(self.equity),
            'monthly_income': float(self.monthly_income) if self.monthly_income else 0.0,
            'monthly_expenses': float(self.monthly_expenses) if self.monthly_expenses else 0.0,
            'net_monthly_income': float(self.net_monthly_income),
            'annual_roi': float(self.annual_roi),
            'cap_rate': float(self.cap_rate),
            'appreciation': float(self.appreciation),
            'appreciation_percent': float(self.appreciation_percent),
            'bedrooms': self.bedrooms,
            'bathrooms': float(self.bathrooms) if self.bathrooms else None,
            'square_feet': self.square_feet,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'last_valuation_date': self.last_valuation_date.isoformat() if self.last_valuation_date else None
        }

    def __repr__(self):
        return f'<RealEstate {self.property_name or self.address} ({self.property_type})>'


# Create indexes
db.Index('idx_accounts_user_type', Account.user_id, Account.account_type)
db.Index('idx_assets_user_type', Asset.user_id, Asset.asset_type)
db.Index('idx_assets_symbol', Asset.symbol)
db.Index('idx_real_estate_user_type', RealEstate.user_id, RealEstate.property_type)
