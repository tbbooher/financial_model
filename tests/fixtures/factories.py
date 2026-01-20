"""
Family Office Platform - Factory Boy Factories

Test data factories for generating realistic test objects.
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

from app import db
from app.models import User, Account, Asset, RealEstate, Transaction, AgentTask


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration."""

    class Meta:
        abstract = True
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'


class UserFactory(BaseFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    risk_tolerance = factory.Iterator(['conservative', 'moderate', 'aggressive'])
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)

    @factory.lazy_attribute
    def password_hash(self):
        from werkzeug.security import generate_password_hash
        return generate_password_hash('TestPassword123!')


class AccountFactory(BaseFactory):
    """Factory for creating Account instances."""

    class Meta:
        model = Account

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    account_name = factory.Faker('company')
    account_type = factory.Iterator(['brokerage', 'retirement', 'checking', 'savings'])
    institution = factory.Faker('company')
    balance = factory.LazyFunction(lambda: Decimal(str(round(factory.Faker('pyfloat', min_value=10000, max_value=1000000).evaluate(None, None, None), 2))))
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)


class AssetFactory(BaseFactory):
    """Factory for creating Asset instances."""

    class Meta:
        model = Asset

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    asset_type = factory.Iterator(['stock', 'etf', 'bond', 'mutual_fund'])
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'SPY', 'QQQ', 'AGG', 'BND'])
    name = factory.LazyAttribute(lambda obj: f'{obj.symbol} Stock')
    quantity = factory.LazyFunction(lambda: Decimal(str(round(factory.Faker('pyfloat', min_value=10, max_value=1000).evaluate(None, None, None), 6))))
    cost_basis = factory.LazyFunction(lambda: Decimal(str(round(factory.Faker('pyfloat', min_value=1000, max_value=100000).evaluate(None, None, None), 2))))
    current_value = factory.LazyAttribute(lambda obj: obj.cost_basis * Decimal(str(round(factory.Faker('pyfloat', min_value=0.8, max_value=1.5).evaluate(None, None, None), 4))))
    last_updated = factory.LazyFunction(datetime.utcnow)


class RealEstateFactory(BaseFactory):
    """Factory for creating RealEstate instances."""

    class Meta:
        model = RealEstate

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    property_type = factory.Iterator(['primary', 'rental', 'commercial', 'land'])
    address = factory.Faker('address')
    purchase_price = factory.LazyFunction(lambda: Decimal(str(round(factory.Faker('pyfloat', min_value=100000, max_value=2000000).evaluate(None, None, None), 2))))
    current_value = factory.LazyAttribute(lambda obj: obj.purchase_price * Decimal(str(round(factory.Faker('pyfloat', min_value=0.9, max_value=1.5).evaluate(None, None, None), 4))))
    monthly_income = factory.LazyFunction(lambda: Decimal(str(round(factory.Faker('pyfloat', min_value=0, max_value=5000).evaluate(None, None, None), 2))))
    monthly_expenses = factory.LazyFunction(lambda: Decimal(str(round(factory.Faker('pyfloat', min_value=200, max_value=1500).evaluate(None, None, None), 2))))
    purchase_date = factory.LazyFunction(lambda: datetime.now(timezone.utc).date() - timedelta(days=factory.Faker('random_int', min=365, max=3650).evaluate(None, None, None)))


class TransactionFactory(BaseFactory):
    """Factory for creating Transaction instances."""

    class Meta:
        model = Transaction

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    transaction_type = factory.Iterator(['buy', 'sell', 'dividend', 'transfer'])
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'SPY'])
    quantity = factory.LazyFunction(lambda: Decimal(str(round(factory.Faker('pyfloat', min_value=1, max_value=100).evaluate(None, None, None), 6))))
    price = factory.LazyFunction(lambda: Decimal(str(round(factory.Faker('pyfloat', min_value=50, max_value=500).evaluate(None, None, None), 2))))
    total_amount = factory.LazyAttribute(lambda obj: obj.quantity * obj.price)
    transaction_date = factory.LazyFunction(datetime.utcnow)


class AgentTaskFactory(BaseFactory):
    """Factory for creating AgentTask instances."""

    class Meta:
        model = AgentTask

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    agent_type = factory.Iterator(['cfa', 'cfp', 'cio', 'accountant', 'quant_risk', 'quant_strategy'])
    task_type = factory.Iterator(['full_analysis', 'quick_review', 'specific_analysis'])
    status = factory.Iterator(['pending', 'processing', 'completed', 'failed'])
    confidence_score = factory.LazyFunction(lambda: round(factory.Faker('pyfloat', min_value=0.5, max_value=1.0).evaluate(None, None, None), 4))
    created_at = factory.LazyFunction(datetime.utcnow)


def create_sample_portfolio(user):
    """Create a complete sample portfolio for a user."""
    accounts = AccountFactory.create_batch(3, user=user)
    assets = AssetFactory.create_batch(10, user=user)
    real_estate = RealEstateFactory.create_batch(2, user=user)
    transactions = TransactionFactory.create_batch(20, user=user)

    return {
        'accounts': accounts,
        'assets': assets,
        'real_estate': real_estate,
        'transactions': transactions
    }
