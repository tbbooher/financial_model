"""
Family Office Platform - Transaction Model

Defines the Transaction model for tracking financial transactions
including trades, deposits, withdrawals, and dividends.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.dialects.postgresql import UUID

from app import db


class Transaction(db.Model):
    """
    Financial transaction model.

    Records all financial transactions including:
    - Buy/Sell trades
    - Deposits/Withdrawals
    - Dividends and interest
    - Fees and expenses
    - Transfers between accounts
    """

    __tablename__ = 'transactions'

    # Primary Key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey('accounts.id'), nullable=True, index=True)
    asset_id = db.Column(UUID(as_uuid=True), db.ForeignKey('assets.id'), nullable=True)

    # Transaction Type
    transaction_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: buy, sell, deposit, withdrawal, dividend, interest, fee, transfer_in, transfer_out, split, merger

    # Asset Details
    symbol = db.Column(db.String(20), index=True)
    asset_name = db.Column(db.String(255))
    asset_type = db.Column(db.String(50))

    # Transaction Details
    quantity = db.Column(db.Numeric(15, 6))
    price = db.Column(db.Numeric(15, 6))
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    fees = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))
    commission = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))

    # For transfers
    related_account_id = db.Column(UUID(as_uuid=True), db.ForeignKey('accounts.id'))
    related_transaction_id = db.Column(UUID(as_uuid=True))

    # Cost Basis Tracking
    cost_basis = db.Column(db.Numeric(15, 2))
    realized_gain_loss = db.Column(db.Numeric(15, 2))
    holding_period = db.Column(db.String(20))  # short_term, long_term

    # Tax Information
    is_wash_sale = db.Column(db.Boolean, default=False)
    wash_sale_disallowed = db.Column(db.Numeric(15, 2))
    tax_lot_id = db.Column(db.String(100))

    # Settlement
    transaction_date = db.Column(db.DateTime, nullable=False, index=True)
    settlement_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='completed')  # pending, completed, cancelled, failed

    # External Reference
    external_id = db.Column(db.String(255))  # ID from external system (Plaid, broker)
    source = db.Column(db.String(50))  # plaid, manual, import

    # Description and Notes
    description = db.Column(db.Text)
    notes = db.Column(db.Text)

    # Additional Data
    extra_data = db.Column(db.JSON)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def net_amount(self) -> Decimal:
        """Calculate net amount after fees."""
        total = self.total_amount or Decimal('0.00')
        fees = self.fees or Decimal('0.00')
        commission = self.commission or Decimal('0.00')

        if self.transaction_type in ['buy', 'deposit', 'transfer_in']:
            return total + fees + commission
        else:
            return total - fees - commission

    @property
    def average_price(self) -> Decimal:
        """Calculate average price per share including fees."""
        if not self.quantity or self.quantity == 0:
            return Decimal('0.00')
        return self.net_amount / self.quantity

    @property
    def is_taxable_event(self) -> bool:
        """Check if this transaction is a taxable event."""
        taxable_types = ['sell', 'dividend', 'interest']
        return self.transaction_type in taxable_types

    @classmethod
    def create_buy(cls, user_id, account_id, symbol, quantity, price, fees=None, **kwargs):
        """Factory method for creating a buy transaction."""
        total = quantity * price
        return cls(
            user_id=user_id,
            account_id=account_id,
            transaction_type='buy',
            symbol=symbol.upper() if symbol else None,
            quantity=quantity,
            price=price,
            total_amount=total,
            fees=fees or Decimal('0.00'),
            transaction_date=kwargs.get('transaction_date', datetime.utcnow()),
            **{k: v for k, v in kwargs.items() if k != 'transaction_date'}
        )

    @classmethod
    def create_sell(cls, user_id, account_id, symbol, quantity, price, cost_basis=None, fees=None, **kwargs):
        """Factory method for creating a sell transaction."""
        total = quantity * price
        realized_gain = (total - cost_basis) if cost_basis else None

        return cls(
            user_id=user_id,
            account_id=account_id,
            transaction_type='sell',
            symbol=symbol.upper() if symbol else None,
            quantity=quantity,
            price=price,
            total_amount=total,
            cost_basis=cost_basis,
            realized_gain_loss=realized_gain,
            fees=fees or Decimal('0.00'),
            transaction_date=kwargs.get('transaction_date', datetime.utcnow()),
            **{k: v for k, v in kwargs.items() if k != 'transaction_date'}
        )

    @classmethod
    def create_dividend(cls, user_id, account_id, symbol, amount, **kwargs):
        """Factory method for creating a dividend transaction."""
        return cls(
            user_id=user_id,
            account_id=account_id,
            transaction_type='dividend',
            symbol=symbol.upper() if symbol else None,
            total_amount=amount,
            transaction_date=kwargs.get('transaction_date', datetime.utcnow()),
            **{k: v for k, v in kwargs.items() if k != 'transaction_date'}
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'account_id': str(self.account_id) if self.account_id else None,
            'transaction_type': self.transaction_type,
            'symbol': self.symbol,
            'asset_name': self.asset_name,
            'quantity': float(self.quantity) if self.quantity else None,
            'price': float(self.price) if self.price else None,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'fees': float(self.fees) if self.fees else 0.0,
            'commission': float(self.commission) if self.commission else 0.0,
            'net_amount': float(self.net_amount),
            'cost_basis': float(self.cost_basis) if self.cost_basis else None,
            'realized_gain_loss': float(self.realized_gain_loss) if self.realized_gain_loss else None,
            'holding_period': self.holding_period,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'settlement_date': self.settlement_date.isoformat() if self.settlement_date else None,
            'status': self.status,
            'description': self.description,
            'source': self.source,
            'is_taxable_event': self.is_taxable_event
        }

    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.symbol} {self.total_amount}>'


# Create indexes
db.Index('idx_transactions_user_date', Transaction.user_id, Transaction.transaction_date)
db.Index('idx_transactions_account_date', Transaction.account_id, Transaction.transaction_date)
db.Index('idx_transactions_type', Transaction.transaction_type)
db.Index('idx_transactions_symbol_date', Transaction.symbol, Transaction.transaction_date)
