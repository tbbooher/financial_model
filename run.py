#!/usr/bin/env python3
"""
Family Office Platform - Application Entry Point

This is the main entry point for the Family Office Platform Flask application.
It creates and configures the Flask app with all necessary extensions and blueprints.
"""

import os
from app import create_app, db
from app.models import User, Account, Asset, RealEstate, Transaction, AgentTask
from flask.cli import with_appcontext
import click

# Create Flask application instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Account': Account,
        'Asset': Asset,
        'RealEstate': RealEstate,
        'Transaction': Transaction,
        'AgentTask': AgentTask
    }

@app.cli.command()
@with_appcontext
def init_db():
    """Initialize the database with tables and seed data"""
    click.echo('Initializing database...')
    db.create_all()
    
    # Create seed data for development
    if app.config['FLASK_ENV'] == 'development':
        create_seed_data()
    
    click.echo('Database initialized successfully!')

@app.cli.command()
@with_appcontext
def seed_data():
    """Create seed data for development and testing"""
    create_seed_data()
    click.echo('Seed data created successfully!')

def create_seed_data():
    """Create initial seed data for development"""
    from app.services.auth_service import AuthService
    from decimal import Decimal
    from datetime import datetime, date
    
    # Create test user if not exists
    if not User.query.filter_by(email='demo@familyoffice.com').first():
        auth_service = AuthService()
        user = auth_service.create_user(
            email='demo@familyoffice.com',
            password='DemoPassword123!',
            first_name='Demo',
            last_name='User',
            net_worth=Decimal('6900557.00'),
            risk_tolerance='moderate'
        )
        
        # Create sample accounts
        accounts_data = [
            {
                'account_type': 'brokerage',
                'account_name': 'Main Brokerage Account',
                'institution': 'Fidelity',
                'current_balance': Decimal('457291.00')
            },
            {
                'account_type': 'retirement',
                'account_name': '401(k) Account',
                'institution': 'Vanguard',
                'current_balance': Decimal('1500000.00')
            },
            {
                'account_type': 'retirement',
                'account_name': 'Roth IRA',
                'institution': 'Charles Schwab',
                'current_balance': Decimal('610265.00')
            },
            {
                'account_type': '529',
                'account_name': 'Education Savings',
                'institution': 'Vanguard',
                'current_balance': Decimal('75640.00')
            },
            {
                'account_type': 'bank',
                'account_name': 'Primary Checking',
                'institution': 'Chase',
                'current_balance': Decimal('131196.00')
            }
        ]
        
        for account_data in accounts_data:
            account = Account(
                user_id=user.id,
                **account_data,
                last_synced=datetime.utcnow(),
                is_active=True
            )
            db.session.add(account)
        
        # Create sample assets
        assets_data = [
            {
                'asset_type': 'stock',
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'quantity': Decimal('500.0'),
                'cost_basis': Decimal('75000.00'),
                'current_value': Decimal('95000.00')
            },
            {
                'asset_type': 'stock',
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'quantity': Decimal('300.0'),
                'cost_basis': Decimal('60000.00'),
                'current_value': Decimal('85000.00')
            },
            {
                'asset_type': 'etf',
                'symbol': 'VTI',
                'name': 'Vanguard Total Stock Market ETF',
                'quantity': Decimal('1000.0'),
                'cost_basis': Decimal('200000.00'),
                'current_value': Decimal('235000.00')
            },
            {
                'asset_type': 'startup_equity',
                'symbol': 'CONFIDENCIAL',
                'name': 'Confidencial Startup',
                'quantity': Decimal('1.0'),
                'cost_basis': Decimal('50000.00'),
                'current_value': Decimal('100000.00')
            }
        ]
        
        for asset_data in assets_data:
            asset = Asset(
                user_id=user.id,
                **asset_data,
                last_updated=datetime.utcnow()
            )
            db.session.add(asset)
        
        # Create sample real estate
        real_estate_data = [
            {
                'property_type': 'primary',
                'address': '4912 Riverbend Drive',
                'purchase_price': Decimal('650000.00'),
                'current_value': Decimal('803773.00'),
                'monthly_income': Decimal('0.00'),
                'monthly_expenses': Decimal('2500.00'),
                'purchase_date': date(2018, 6, 15)
            },
            {
                'property_type': 'rental',
                'address': '3623 Tupelo Place',
                'purchase_price': Decimal('380000.00'),
                'current_value': Decimal('474372.00'),
                'monthly_income': Decimal('2800.00'),
                'monthly_expenses': Decimal('800.00'),
                'purchase_date': date(2019, 3, 20)
            },
            {
                'property_type': 'rental',
                'address': '211 Brian Circle',
                'purchase_price': Decimal('295000.00'),
                'current_value': Decimal('367000.00'),
                'monthly_income': Decimal('2200.00'),
                'monthly_expenses': Decimal('600.00'),
                'purchase_date': date(2020, 8, 10)
            }
        ]
        
        for property_data in real_estate_data:
            property_obj = RealEstate(
                user_id=user.id,
                **property_data,
                last_valuation_date=date.today()
            )
            db.session.add(property_obj)
        
        db.session.commit()
        print(f"Created demo user: {user.email}")

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }

if __name__ == '__main__':
    # Development server configuration
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )