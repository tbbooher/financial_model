"""
Family Office Platform - Model Unit Tests

Tests for database models and their methods.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from app.models import User, Account, Asset, RealEstate, Transaction, AgentTask


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, db_session):
        """Test creating a new user."""
        user = User(
            email='newuser@example.com',
            first_name='New',
            last_name='User',
            risk_tolerance='moderate'
        )
        user.set_password('SecurePassword123!')

        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == 'newuser@example.com'
        assert user.first_name == 'New'
        assert user.is_active is True

    def test_password_hashing(self, db_session):
        """Test password is properly hashed."""
        user = User(email='pwd@example.com')
        user.set_password('MyPassword123!')

        assert user.password_hash != 'MyPassword123!'
        assert user.check_password('MyPassword123!') is True
        assert user.check_password('WrongPassword') is False

    def test_user_to_dict(self, sample_user):
        """Test user serialization to dictionary."""
        user_dict = sample_user.to_dict()

        assert 'id' in user_dict
        assert user_dict['email'] == sample_user.email
        assert 'password_hash' not in user_dict  # Should not include sensitive data

    def test_user_to_dict_with_sensitive(self, sample_user):
        """Test user serialization with sensitive data."""
        user_dict = sample_user.to_dict(include_sensitive=True)

        assert 'risk_tolerance' in user_dict
        assert 'created_at' in user_dict


class TestAccountModel:
    """Tests for the Account model."""

    def test_create_account(self, db_session, sample_user):
        """Test creating a new account."""
        account = Account(
            user_id=sample_user.id,
            account_name='Test Account',
            account_type='brokerage',
            institution='Test Bank',
            current_balance=Decimal('50000.00')
        )

        db_session.add(account)
        db_session.commit()

        assert account.id is not None
        assert account.current_balance == Decimal('50000.00')
        assert account.user_id == sample_user.id

    def test_account_to_dict(self, sample_account):
        """Test account serialization."""
        account_dict = sample_account.to_dict()

        assert 'id' in account_dict
        assert account_dict['account_name'] == sample_account.account_name
        assert 'current_balance' in account_dict


class TestAssetModel:
    """Tests for the Asset model."""

    def test_create_asset(self, db_session, sample_user):
        """Test creating a new asset."""
        asset = Asset(
            user_id=sample_user.id,
            asset_type='stock',
            symbol='TSLA',
            name='Tesla Inc.',
            quantity=Decimal('50'),
            cost_basis=Decimal('10000.00'),
            current_value=Decimal('12500.00')
        )

        db_session.add(asset)
        db_session.commit()

        assert asset.id is not None
        assert asset.symbol == 'TSLA'

    def test_unrealized_gain_loss(self, db_session, sample_user):
        """Test unrealized gain/loss calculation."""
        # Asset with gain
        asset_gain = Asset(
            user_id=sample_user.id,
            asset_type='stock',
            symbol='WIN',
            name='Winner Stock',
            quantity=Decimal('100'),
            cost_basis=Decimal('10000.00'),
            current_value=Decimal('15000.00')
        )

        assert asset_gain.unrealized_gain_loss == Decimal('5000.00')

        # Asset with loss
        asset_loss = Asset(
            user_id=sample_user.id,
            asset_type='stock',
            symbol='LOSE',
            name='Loser Stock',
            quantity=Decimal('100'),
            cost_basis=Decimal('10000.00'),
            current_value=Decimal('8000.00')
        )

        assert asset_loss.unrealized_gain_loss == Decimal('-2000.00')

    def test_return_percentage(self, db_session, sample_user):
        """Test return percentage calculation."""
        asset = Asset(
            user_id=sample_user.id,
            asset_type='stock',
            symbol='TEST',
            name='Test Stock',
            quantity=Decimal('100'),
            cost_basis=Decimal('10000.00'),
            current_value=Decimal('12000.00')
        )

        # 20% return (returned as percentage, not decimal)
        assert asset.return_percentage == Decimal('20')

    def test_asset_to_dict(self, sample_assets):
        """Test asset serialization."""
        asset = sample_assets[0]
        asset_dict = asset.to_dict()

        assert 'id' in asset_dict
        assert asset_dict['symbol'] == asset.symbol
        assert 'current_value' in asset_dict


class TestRealEstateModel:
    """Tests for the RealEstate model."""

    def test_create_real_estate(self, db_session, sample_user):
        """Test creating a real estate property."""
        property = RealEstate(
            user_id=sample_user.id,
            property_type='rental',
            address='789 Test Lane',
            purchase_price=Decimal('400000.00'),
            current_value=Decimal('450000.00'),
            monthly_income=Decimal('3000.00'),
            monthly_expenses=Decimal('1000.00'),
            purchase_date=datetime(2022, 1, 1).date()
        )

        db_session.add(property)
        db_session.commit()

        assert property.id is not None
        assert property.property_type == 'rental'

    def test_annual_roi_calculation(self, db_session, sample_user):
        """Test annual ROI calculation for rental property."""
        property = RealEstate(
            user_id=sample_user.id,
            property_type='rental',
            address='Test Address',
            purchase_price=Decimal('200000.00'),
            current_value=Decimal('220000.00'),
            monthly_income=Decimal('2000.00'),
            monthly_expenses=Decimal('500.00')
        )

        # Net annual income = (2000 - 500) * 12 = 18000
        # ROI = 18000 / 200000 * 100 = 9% (returned as percentage)
        assert property.annual_roi == Decimal('9.00')


class TestTransactionModel:
    """Tests for the Transaction model."""

    def test_create_buy_transaction(self, db_session, sample_user, sample_account):
        """Test creating a buy transaction."""
        transaction = Transaction.create_buy(
            user_id=sample_user.id,
            account_id=sample_account.id,
            symbol='AAPL',
            quantity=Decimal('10'),
            price=Decimal('150.00'),
            notes='Test purchase'
        )

        db_session.add(transaction)
        db_session.commit()

        assert transaction.transaction_type == 'buy'
        assert transaction.total_amount == Decimal('1500.00')

    def test_create_sell_transaction(self, db_session, sample_user, sample_account):
        """Test creating a sell transaction."""
        transaction = Transaction.create_sell(
            user_id=sample_user.id,
            account_id=sample_account.id,
            symbol='GOOGL',
            quantity=Decimal('5'),
            price=Decimal('2500.00')
        )

        db_session.add(transaction)
        db_session.commit()

        assert transaction.transaction_type == 'sell'
        assert transaction.total_amount == Decimal('12500.00')


class TestAgentTaskModel:
    """Tests for the AgentTask model."""

    def test_create_agent_task(self, db_session, sample_user):
        """Test creating an agent task."""
        task = AgentTask(
            user_id=sample_user.id,
            agent_type='cfa',
            task_type='full_analysis',
            status='pending'
        )

        db_session.add(task)
        db_session.commit()

        assert task.id is not None
        assert task.status == 'pending'

    def test_agent_task_status_update(self, db_session, sample_user):
        """Test updating agent task status."""
        task = AgentTask(
            user_id=sample_user.id,
            agent_type='cfp',
            task_type='quick_review',
            status='pending'
        )

        db_session.add(task)
        db_session.commit()

        # Update status
        task.status = 'processing'
        db_session.commit()

        assert task.status == 'processing'

        # Complete task
        task.status = 'completed'
        task.confidence_score = Decimal('0.85')
        task.completed_at = datetime.utcnow()
        db_session.commit()

        assert task.status == 'completed'
        assert task.confidence_score == Decimal('0.85')
        assert task.completed_at is not None
