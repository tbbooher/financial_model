# Family Office Platform - Development Guide for Claude

## Project Overview
This guide provides comprehensive instructions for developing a sophisticated family office platform in Python Flask. The system manages a $6.9M portfolio through specialized AI agents and provides institutional-grade financial analysis.

## Development Philosophy

### Code Quality Standards
- **Precision First**: Financial calculations must be mathematically accurate to 6 decimal places
- **Security by Design**: All financial data encrypted, authenticated, and audited
- **Performance Critical**: Sub-second response times for real-time portfolio updates
- **Regulatory Compliance**: Built with SOC 2, GDPR, and financial regulations in mind

### Architecture Principles
- **Microservices**: Separate services for agents, portfolio engine, and data pipeline
- **Event-Driven**: Asynchronous processing for heavy financial calculations
- **API-First**: RESTful design with comprehensive OpenAPI documentation
- **Testable**: Property-based testing for financial correctness properties

## Technology Stack

### Core Framework
```python
# Primary Stack
Flask==2.3.3              # Web framework
SQLAlchemy==2.0.21         # ORM for database operations
Alembic==1.12.0           # Database migrations
Celery==5.3.2             # Asynchronous task processing
Redis==4.6.0              # Caching and message broker
PostgreSQL==14            # Primary database
```

### Financial Libraries
```python
# Quantitative Analysis
numpy==1.24.3             # Numerical computations
pandas==2.0.3             # Data manipulation
scipy==1.11.2             # Statistical functions
scikit-learn==1.3.0       # Machine learning for risk models
yfinance==0.2.18          # Market data retrieval
quantlib==1.31            # Quantitative finance library
```

### Security & Authentication
```python
# Security Stack
Flask-JWT-Extended==4.5.2  # JWT authentication
cryptography==41.0.4       # Encryption utilities
bcrypt==4.0.1             # Password hashing
python-dotenv==1.0.0      # Environment management
```

## Project Structure

```
family-office-platform/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── config.py                   # Configuration management
│   ├── models/                     # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py                 # User and authentication
│   │   ├── portfolio.py            # Portfolio and assets
│   │   ├── transactions.py         # Financial transactions
│   │   └── agents.py               # Agent task tracking
│   ├── agents/                     # AI Agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Abstract base class
│   │   ├── cfa_agent.py            # CFA investment analysis
│   │   ├── cfp_agent.py            # CFP financial planning
│   │   ├── cio_agent.py            # Chief Investment Officer
│   │   ├── accountant_agent.py     # Tax and compliance
│   │   ├── quant_analyst.py        # Quantitative analysis
│   │   └── agent_manager.py        # Agent orchestration
│   ├── services/                   # Business logic services
│   │   ├── __init__.py
│   │   ├── portfolio_service.py    # Portfolio calculations
│   │   ├── risk_service.py         # Risk management
│   │   ├── capm_service.py         # CAPM analysis
│   │   ├── data_service.py         # External data integration
│   │   └── auth_service.py         # Authentication logic
│   ├── api/                        # REST API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication endpoints
│   │   ├── portfolio.py            # Portfolio management
│   │   ├── agents.py               # Agent interaction
│   │   ├── analytics.py            # Financial analytics
│   │   └── admin.py                # Administrative functions
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   ├── encryption.py           # Data encryption utilities
│   │   ├── validators.py           # Input validation
│   │   ├── formatters.py           # Data formatting
│   │   └── exceptions.py           # Custom exceptions
│   └── tasks/                      # Celery background tasks
│       ├── __init__.py
│       ├── portfolio_tasks.py      # Portfolio calculations
│       ├── data_sync_tasks.py      # External data synchronization
│       └── agent_tasks.py          # Agent processing tasks
├── migrations/                     # Database migrations
├── tests/                          # Test suite
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   ├── property/                   # Property-based tests
│   └── fixtures/                   # Test data fixtures
├── docker/                         # Docker configuration
├── docs/                           # Documentation
├── requirements.txt                # Python dependencies
├── docker-compose.yml              # Development environment
├── .env.example                    # Environment variables template
└── run.py                          # Application entry point
```

## Development Workflow

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Start Redis (required for Celery)
redis-server

# Start Celery worker (in separate terminal)
celery -A app.celery worker --loglevel=info
```

### 2. Database Models Implementation

#### User Model
```python
# app/models/user.py
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    net_worth = db.Column(db.Numeric(15, 2))
    risk_tolerance = db.Column(db.String(20))  # 'conservative', 'moderate', 'aggressive'
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    accounts = db.relationship('Account', backref='user', lazy='dynamic')
    assets = db.relationship('Asset', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def total_assets(self):
        return sum(asset.current_value for asset in self.assets)
    
    @property
    def total_liabilities(self):
        # Calculate from mortgage/loan data
        return sum(account.balance for account in self.accounts 
                  if account.account_type == 'liability')
```

#### Portfolio Model
```python
# app/models/portfolio.py
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Asset(db.Model):
    __tablename__ = 'assets'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)  # 'stock', 'bond', 'real_estate'
    symbol = db.Column(db.String(20))
    name = db.Column(db.String(255))
    quantity = db.Column(db.Numeric(15, 6))
    cost_basis = db.Column(db.Numeric(15, 2))
    current_value = db.Column(db.Numeric(15, 2))
    last_updated = db.Column(db.DateTime, default=db.func.now())
    
    @property
    def unrealized_gain_loss(self):
        if self.cost_basis and self.current_value:
            return self.current_value - self.cost_basis
        return 0
    
    @property
    def return_percentage(self):
        if self.cost_basis and self.cost_basis != 0:
            return (self.current_value - self.cost_basis) / self.cost_basis
        return 0

class RealEstate(db.Model):
    __tablename__ = 'real_estate'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    property_type = db.Column(db.String(50))  # 'primary', 'rental', 'commercial'
    address = db.Column(db.Text)
    purchase_price = db.Column(db.Numeric(15, 2))
    current_value = db.Column(db.Numeric(15, 2))
    monthly_income = db.Column(db.Numeric(10, 2))
    monthly_expenses = db.Column(db.Numeric(10, 2))
    purchase_date = db.Column(db.Date)
    last_valuation_date = db.Column(db.Date)
    
    @property
    def annual_roi(self):
        if self.purchase_price and self.monthly_income and self.monthly_expenses:
            net_annual_income = (self.monthly_income - self.monthly_expenses) * 12
            return net_annual_income / self.purchase_price
        return 0
```

### 3. Agent System Implementation

#### Base Agent Class
```python
# app/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
import logging

@dataclass
class AgentResponse:
    agent_type: str
    recommendations: List[Dict[str, Any]]
    confidence_score: float
    reasoning: str
    data_sources: List[str]
    timestamp: str

class BaseAgent(ABC):
    def __init__(self, user_id: str, portfolio_data: Dict[str, Any]):
        self.user_id = user_id
        self.portfolio_data = portfolio_data
        self.agent_type = self.__class__.__name__.lower().replace('agent', '')
        self.logger = logging.getLogger(f'agent.{self.agent_type}')
    
    @abstractmethod
    def analyze(self) -> AgentResponse:
        """Perform agent-specific analysis"""
        pass
    
    @abstractmethod
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Generate specific recommendations"""
        pass
    
    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """Calculate confidence score based on data quality and market conditions"""
        # Implement confidence calculation logic
        return min(sum(factors.values()) / len(factors), 1.0)
    
    def _log_analysis(self, analysis_type: str, result: Any):
        """Log analysis for audit trail"""
        self.logger.info(f"Analysis completed: {analysis_type} for user {self.user_id}")
```

#### CFA Agent Implementation
```python
# app/agents/cfa_agent.py
from app.agents.base_agent import BaseAgent, AgentResponse
from app.services.capm_service import CAPMService
from app.services.risk_service import RiskService
import numpy as np
from datetime import datetime

class CFAAgent(BaseAgent):
    """Chartered Financial Analyst - Investment Analysis and Portfolio Management"""
    
    def __init__(self, user_id: str, portfolio_data: Dict[str, Any]):
        super().__init__(user_id, portfolio_data)
        self.capm_service = CAPMService()
        self.risk_service = RiskService()
    
    def analyze(self) -> AgentResponse:
        """Comprehensive investment analysis"""
        try:
            # Perform various analyses
            portfolio_metrics = self._calculate_portfolio_metrics()
            risk_analysis = self._perform_risk_analysis()
            capm_analysis = self._perform_capm_analysis()
            recommendations = self.get_recommendations()
            
            confidence_factors = {
                'data_quality': self._assess_data_quality(),
                'market_stability': self._assess_market_conditions(),
                'portfolio_size': min(self.portfolio_data.get('total_value', 0) / 1000000, 1.0)
            }
            
            return AgentResponse(
                agent_type=self.agent_type,
                recommendations=recommendations,
                confidence_score=self._calculate_confidence(confidence_factors),
                reasoning=self._generate_analysis_reasoning(portfolio_metrics, risk_analysis),
                data_sources=['market_data', 'portfolio_holdings', 'risk_models', 'capm_model'],
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"CFA analysis failed: {str(e)}")
            raise
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Generate investment recommendations"""
        recommendations = []
        
        # Asset allocation analysis
        current_allocation = self._calculate_current_allocation()
        target_allocation = self._calculate_target_allocation()
        
        if self._needs_rebalancing(current_allocation, target_allocation):
            recommendations.append({
                'type': 'rebalancing',
                'priority': 'high',
                'description': 'Portfolio rebalancing recommended',
                'details': self._generate_rebalancing_plan(current_allocation, target_allocation),
                'expected_impact': 'Reduce risk by 15%, maintain expected return'
            })
        
        # Individual security analysis
        underperforming_assets = self._identify_underperforming_assets()
        if underperforming_assets:
            recommendations.append({
                'type': 'security_review',
                'priority': 'medium',
                'description': f'Review {len(underperforming_assets)} underperforming positions',
                'details': underperforming_assets,
                'expected_impact': 'Potential 3-5% improvement in returns'
            })
        
        return recommendations
    
    def _calculate_portfolio_metrics(self) -> Dict[str, float]:
        """Calculate key portfolio performance metrics"""
        returns = self._get_portfolio_returns()
        
        return {
            'total_return_1y': self._calculate_total_return(returns, 252),
            'volatility': np.std(returns) * np.sqrt(252),
            'sharpe_ratio': self._calculate_sharpe_ratio(returns),
            'max_drawdown': self._calculate_max_drawdown(returns),
            'beta': self.camp_service.calculate_portfolio_beta(self.portfolio_data),
            'alpha': self._calculate_alpha(returns)
        }
    
    def _perform_camp_analysis(self) -> Dict[str, Any]:
        """Perform Capital Asset Pricing Model analysis"""
        return {
            'portfolio_beta': self.capm_service.calculate_portfolio_beta(self.portfolio_data),
            'expected_return': self.capm_service.calculate_expected_return(self.portfolio_data),
            'security_market_line': self.capm_service.generate_sml_data(self.portfolio_data),
            'asset_pricing_analysis': self.capm_service.analyze_individual_assets(self.portfolio_data)
        }
```

### 4. CAPM Service Implementation

```python
# app/services/capm_service.py
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
import yfinance as yf
from app.utils.exceptions import CalculationError

class CAPMService:
    def __init__(self, risk_free_rate: float = 0.02, market_symbol: str = '^GSPC'):
        self.risk_free_rate = risk_free_rate
        self.market_symbol = market_symbol
        self.market_data = None
    
    def calculate_beta(self, asset_symbol: str, period: str = '2y') -> float:
        """Calculate beta coefficient for an individual asset"""
        try:
            # Get asset and market data
            asset_data = yf.download(asset_symbol, period=period)['Adj Close']
            market_data = yf.download(self.market_symbol, period=period)['Adj Close']
            
            # Calculate returns
            asset_returns = asset_data.pct_change().dropna()
            market_returns = market_data.pct_change().dropna()
            
            # Align data
            aligned_data = pd.concat([asset_returns, market_returns], axis=1).dropna()
            
            if len(aligned_data) < 50:  # Minimum data points
                raise CalculationError(f"Insufficient data for beta calculation: {asset_symbol}")
            
            # Calculate beta using covariance method
            covariance = np.cov(aligned_data.iloc[:, 0], aligned_data.iloc[:, 1])[0][1]
            market_variance = np.var(aligned_data.iloc[:, 1])
            
            beta = covariance / market_variance
            
            return round(beta, 4)
            
        except Exception as e:
            raise CalculationError(f"Beta calculation failed for {asset_symbol}: {str(e)}")
    
    def calculate_expected_return(self, beta: float, market_return: float = None) -> float:
        """Calculate expected return using CAPM formula"""
        if market_return is None:
            market_return = self._get_market_expected_return()
        
        expected_return = self.risk_free_rate + beta * (market_return - self.risk_free_rate)
        return round(expected_return, 4)
    
    def calculate_portfolio_beta(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate weighted portfolio beta"""
        total_value = portfolio_data.get('total_value', 0)
        if total_value == 0:
            return 0
        
        weighted_beta = 0
        
        for asset in portfolio_data.get('assets', []):
            if asset.get('asset_type') in ['stock', 'etf', 'mutual_fund']:
                weight = asset.get('current_value', 0) / total_value
                asset_beta = self.calculate_beta(asset.get('symbol', ''))
                weighted_beta += weight * asset_beta
        
        return round(weighted_beta, 4)
    
    def generate_security_market_line(self, beta_range: Tuple[float, float] = (0, 2.0), 
                                    points: int = 100) -> Dict[str, List[float]]:
        """Generate Security Market Line data points"""
        market_return = self._get_market_expected_return()
        betas = np.linspace(beta_range[0], beta_range[1], points)
        expected_returns = [self.calculate_expected_return(beta, market_return) for beta in betas]
        
        return {
            'betas': betas.tolist(),
            'expected_returns': expected_returns,
            'risk_free_rate': self.risk_free_rate,
            'market_return': market_return
        }
    
    def analyze_asset_pricing(self, portfolio_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze if assets are fairly priced according to CAPM"""
        analysis_results = []
        
        for asset in portfolio_data.get('assets', []):
            if asset.get('asset_type') in ['stock', 'etf']:
                symbol = asset.get('symbol')
                current_return = asset.get('return_1y', 0)
                beta = self.calculate_beta(symbol)
                expected_return = self.calculate_expected_return(beta)
                
                alpha = current_return - expected_return
                
                analysis_results.append({
                    'symbol': symbol,
                    'name': asset.get('name'),
                    'beta': beta,
                    'expected_return': expected_return,
                    'actual_return': current_return,
                    'alpha': alpha,
                    'valuation': self._determine_valuation(alpha),
                    'recommendation': self._generate_recommendation(alpha, beta)
                })
        
        return analysis_results
    
    def _get_market_expected_return(self) -> float:
        """Calculate market expected return based on historical data"""
        try:
            market_data = yf.download(self.market_symbol, period='10y')['Adj Close']
            returns = market_data.pct_change().dropna()
            annual_return = (1 + returns.mean()) ** 252 - 1
            return round(annual_return, 4)
        except:
            return 0.08  # Default market return assumption
    
    def _determine_valuation(self, alpha: float) -> str:
        """Determine if asset is overvalued, undervalued, or fairly valued"""
        if alpha > 0.02:
            return 'undervalued'
        elif alpha < -0.02:
            return 'overvalued'
        else:
            return 'fairly_valued'
    
    def _generate_recommendation(self, alpha: float, beta: float) -> str:
        """Generate investment recommendation based on CAPM analysis"""
        if alpha > 0.05:
            return 'strong_buy'
        elif alpha > 0.02:
            return 'buy'
        elif alpha < -0.05:
            return 'strong_sell'
        elif alpha < -0.02:
            return 'sell'
        else:
            return 'hold'
```

### 5. API Implementation

```python
# app/api/portfolio.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.portfolio_service import PortfolioService
from app.services.capm_service import CAPMService
from app.utils.validators import validate_portfolio_request
from app.utils.exceptions import ValidationError, CalculationError

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/v1/portfolio')

@portfolio_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_portfolio_summary():
    """Get comprehensive portfolio summary"""
    try:
        user_id = get_jwt_identity()
        portfolio_service = PortfolioService(user_id)
        
        summary = portfolio_service.get_portfolio_summary()
        
        return jsonify({
            'status': 'success',
            'data': summary,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@portfolio_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_portfolio_performance():
    """Get portfolio performance metrics"""
    try:
        user_id = get_jwt_identity()
        period = request.args.get('period', '1Y')
        
        portfolio_service = PortfolioService(user_id)
        performance = portfolio_service.calculate_performance_metrics(period)
        
        return jsonify({
            'status': 'success',
            'data': performance,
            'period': period
        }), 200
        
    except CalculationError as e:
        return jsonify({
            'status': 'error',
            'message': f'Performance calculation failed: {str(e)}'
        }), 400

@portfolio_bp.route('/capm-analysis', methods=['GET'])
@jwt_required()
def get_capm_analysis():
    """Get CAPM analysis for portfolio"""
    try:
        user_id = get_jwt_identity()
        
        portfolio_service = PortfolioService(user_id)
        capm_service = CAPMService()
        
        portfolio_data = portfolio_service.get_portfolio_data()
        capm_analysis = {
            'portfolio_beta': capm_service.calculate_portfolio_beta(portfolio_data),
            'security_market_line': camp_service.generate_security_market_line(),
            'asset_analysis': capm_service.analyze_asset_pricing(portfolio_data)
        }
        
        return jsonify({
            'status': 'success',
            'data': capm_analysis
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

## Testing Strategy

### Property-Based Testing
```python
# tests/property/test_portfolio_properties.py
import hypothesis.strategies as st
from hypothesis import given, assume
from app.services.portfolio_service import PortfolioService
from app.services.capm_service import CAPMService

class TestPortfolioProperties:
    
    @given(st.lists(st.floats(min_value=0, max_value=1000000), min_size=1, max_size=20))
    def test_portfolio_sum_property(self, asset_values):
        """Property: Sum of individual assets equals total portfolio value"""
        assume(all(v >= 0 for v in asset_values))
        
        portfolio_service = PortfolioService()
        total_calculated = portfolio_service.calculate_total_value(asset_values)
        expected_total = sum(asset_values)
        
        assert abs(total_calculated - expected_total) < 0.01
    
    @given(st.floats(min_value=-2.0, max_value=3.0))
    def test_capm_expected_return_bounds(self, beta):
        """Property: CAPM expected returns should be within reasonable bounds"""
        capm_service = CAPMService(risk_free_rate=0.02)
        market_return = 0.08
        
        expected_return = capm_service.calculate_expected_return(beta, market_return)
        
        # Expected return should be between risk-free rate and reasonable upper bound
        assert -0.5 <= expected_return <= 0.5
        
        # For beta = 1, expected return should equal market return
        if abs(beta - 1.0) < 0.001:
            assert abs(expected_return - market_return) < 0.001
```

## Security Implementation

### Data Encryption
```python
# app/utils/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionService:
    def __init__(self, password: bytes = None):
        if password is None:
            password = os.environ.get('ENCRYPTION_KEY', '').encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'family_office_salt',  # Use proper random salt in production
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher_suite = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
```

## Deployment Configuration

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "run:app"]
```

## Performance Optimization

### Caching Strategy
```python
# app/utils/cache.py
import redis
import json
from functools import wraps
from typing import Any, Callable

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration: int = 300):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Calculate and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator
```

## Monitoring & Logging

### Application Monitoring
```python
# app/utils/monitoring.py
import logging
import time
from functools import wraps
from flask import request, g

def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/family_office.log'),
            logging.StreamHandler()
        ]
    )

def log_performance(func):
    """Decorator to log function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logging.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper
```

## Development Best Practices

### Code Quality Checklist
- [ ] All financial calculations tested with property-based tests
- [ ] Sensitive data encrypted at rest and in transit
- [ ] API endpoints properly authenticated and authorized
- [ ] Database queries optimized with proper indexing
- [ ] Error handling with appropriate logging
- [ ] Input validation on all user inputs
- [ ] Performance monitoring for critical paths
- [ ] Comprehensive test coverage (>90%)
- [ ] Security audit trail for all financial operations
- [ ] Proper configuration management for different environments

### Financial Accuracy Requirements
- All monetary calculations must use `Decimal` type for precision
- Portfolio values must reconcile to the penny
- Performance calculations must match industry standards
- Risk metrics must be mathematically sound
- CAPM calculations must follow academic formulas exactly

This development guide provides the foundation for building a sophisticated, secure, and accurate family office platform. Follow these patterns and practices to ensure the system meets institutional-grade requirements for financial management.