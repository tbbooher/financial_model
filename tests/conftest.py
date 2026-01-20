"""
Family Office Platform - Pytest Configuration and Fixtures

Provides test fixtures, app factory, and database setup for testing.
"""

import pytest
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Set testing environment before importing app
os.environ['FLASK_ENV'] = 'testing'

from app import create_app, db
from app.models import User, Account, Asset, RealEstate, Transaction, AgentTask


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'

    return app


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        email='test@example.com',
        first_name='Test',
        last_name='User',
        risk_tolerance='moderate'
    )
    user.set_password('TestPassword123!')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_account(db_session, sample_user):
    """Create a sample account for testing."""
    account = Account(
        user_id=sample_user.id,
        account_name='Test Brokerage',
        account_type='brokerage',
        institution='Test Bank',
        current_balance=Decimal('100000.00')
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def sample_assets(db_session, sample_user):
    """Create sample assets for testing."""
    assets = [
        Asset(
            user_id=sample_user.id,
            asset_type='stock',
            symbol='AAPL',
            name='Apple Inc.',
            quantity=Decimal('100'),
            cost_basis=Decimal('15000.00'),
            current_value=Decimal('18500.00')
        ),
        Asset(
            user_id=sample_user.id,
            asset_type='stock',
            symbol='GOOGL',
            name='Alphabet Inc.',
            quantity=Decimal('50'),
            cost_basis=Decimal('12500.00'),
            current_value=Decimal('14000.00')
        ),
        Asset(
            user_id=sample_user.id,
            asset_type='etf',
            symbol='SPY',
            name='SPDR S&P 500 ETF',
            quantity=Decimal('200'),
            cost_basis=Decimal('80000.00'),
            current_value=Decimal('90000.00')
        ),
        Asset(
            user_id=sample_user.id,
            asset_type='bond',
            symbol='AGG',
            name='iShares Core US Aggregate Bond ETF',
            quantity=Decimal('500'),
            cost_basis=Decimal('50000.00'),
            current_value=Decimal('48000.00')
        )
    ]

    for asset in assets:
        db_session.add(asset)
    db_session.commit()

    return assets


@pytest.fixture
def sample_real_estate(db_session, sample_user):
    """Create sample real estate for testing."""
    properties = [
        RealEstate(
            user_id=sample_user.id,
            property_type='primary',
            address='123 Main St, City, ST 12345',
            purchase_price=Decimal('500000.00'),
            current_value=Decimal('650000.00'),
            purchase_date=datetime(2020, 1, 15).date()
        ),
        RealEstate(
            user_id=sample_user.id,
            property_type='rental',
            address='456 Oak Ave, Town, ST 67890',
            purchase_price=Decimal('300000.00'),
            current_value=Decimal('350000.00'),
            monthly_income=Decimal('2500.00'),
            monthly_expenses=Decimal('800.00'),
            purchase_date=datetime(2021, 6, 1).date()
        )
    ]

    for prop in properties:
        db_session.add(prop)
    db_session.commit()

    return properties


@pytest.fixture
def sample_portfolio_data(sample_user, sample_assets, sample_real_estate):
    """Create comprehensive portfolio data for testing."""
    total_assets = sum(float(a.current_value) for a in sample_assets)
    total_real_estate = sum(float(p.current_value) for p in sample_real_estate)

    return {
        'user_id': str(sample_user.id),
        'total_value': total_assets + total_real_estate,
        'total_assets': total_assets + total_real_estate,
        'total_liabilities': 0,
        'net_worth': total_assets + total_real_estate,
        'assets': [
            {
                'id': str(a.id),
                'asset_type': a.asset_type,
                'symbol': a.symbol,
                'name': a.name,
                'quantity': float(a.quantity),
                'cost_basis': float(a.cost_basis),
                'current_value': float(a.current_value),
                'return_1y': 0.10
            }
            for a in sample_assets
        ],
        'real_estate': [
            {
                'id': str(p.id),
                'property_type': p.property_type,
                'address': p.address,
                'current_value': float(p.current_value)
            }
            for p in sample_real_estate
        ],
        'breakdown': {
            'stocks': sum(float(a.current_value) for a in sample_assets if a.asset_type == 'stock'),
            'etf': sum(float(a.current_value) for a in sample_assets if a.asset_type == 'etf'),
            'bonds': sum(float(a.current_value) for a in sample_assets if a.asset_type == 'bond'),
            'real_estate': total_real_estate
        }
    }


@pytest.fixture
def auth_headers(app, client, sample_user):
    """Get authentication headers for API requests."""
    from flask_jwt_extended import create_access_token

    with app.app_context():
        token = create_access_token(identity=str(sample_user.id))
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def mock_market_data():
    """Mock market data for testing."""
    return {
        'S&P 500': {'price': 4500.00, 'change': 0.015},
        'NASDAQ': {'price': 14000.00, 'change': 0.020},
        'DOW': {'price': 35000.00, 'change': 0.010}
    }


@pytest.fixture
def mock_stock_price():
    """Mock stock price data for testing."""
    return {
        'symbol': 'AAPL',
        'price': 185.00,
        'change': 2.50,
        'change_percent': 0.0137,
        'volume': 50000000
    }
