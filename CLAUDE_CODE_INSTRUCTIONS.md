# Claude Code Development Instructions

## 🎯 Project Overview
Build a complete Family Office Platform for managing $6.9M+ portfolios with 8 specialized AI agents. This is a comprehensive financial management system requiring institutional-grade accuracy and security.

## 📋 Development Priority Order

### PHASE 1: CRITICAL FOUNDATION (Build First)
1. **Flask App Structure** (`app/__init__.py`, `app/config.py`)
2. **Database Models** (`app/models/` - all model files)
3. **Authentication System** (`app/services/auth_service.py`, `app/api/auth.py`)
4. **Base Agent Framework** (`app/agents/base_agent.py`, `app/agents/agent_manager.py`)

### PHASE 2: CORE FINANCIAL ENGINE (Build Second)
1. **Portfolio Service** (`app/services/portfolio_service.py`)
2. **CAPM Analysis** (`app/services/capm_service.py`)
3. **Risk Management** (`app/services/risk_service.py`)
4. **Portfolio API** (`app/api/portfolio.py`)

### PHASE 3: AI AGENTS (Build Third)
1. **CFA Agent** (`app/agents/cfa_agent.py`)
2. **CFP Agent** (`app/agents/cfp_agent.py`)
3. **CIO Agent** (`app/agents/cio_agent.py`)
4. **Quant Analysts** (`app/agents/quant_analyst.py`)
5. **Supporting Agents** (Accountant, Coach, etc.)

### PHASE 4: DATA INTEGRATION (Build Fourth)
1. **Market Data Service** (`app/services/data_service.py`)
2. **External API Integration** (`app/utils/external_apis.py`)
3. **Background Tasks** (`app/tasks/` - all task files)

### PHASE 5: TESTING & VALIDATION (Build Fifth)
1. **Property-Based Tests** (`tests/property/`)
2. **Unit Tests** (`tests/unit/`)
3. **Integration Tests** (`tests/integration/`)

## 🏗️ File Structure to Build

```
app/
├── __init__.py                    # Flask app factory ⭐ CRITICAL
├── config.py                      # Configuration management ⭐ CRITICAL
├── models/
│   ├── __init__.py               # Model imports ⭐ CRITICAL
│   ├── user.py                   # User model ⭐ CRITICAL
│   ├── portfolio.py              # Asset/Portfolio models ⭐ CRITICAL
│   ├── transactions.py           # Transaction model
│   └── agents.py                 # Agent task model
├── services/
│   ├── __init__.py
│   ├── auth_service.py           # Authentication logic ⭐ CRITICAL
│   ├── portfolio_service.py      # Portfolio calculations ⭐ CRITICAL
│   ├── capm_service.py          # CAPM analysis ⭐ CRITICAL
│   ├── risk_service.py          # Risk management ⭐ CRITICAL
│   └── data_service.py          # External data integration
├── agents/
│   ├── __init__.py
│   ├── base_agent.py            # Base agent class ⭐ CRITICAL
│   ├── agent_manager.py         # Agent orchestration ⭐ CRITICAL
│   ├── cfa_agent.py            # CFA investment analysis
│   ├── cfp_agent.py            # CFP financial planning
│   ├── cio_agent.py            # Chief Investment Officer
│   ├── quant_analyst.py        # Quantitative analysis
│   ├── accountant_agent.py     # Tax optimization
│   ├── coach_agent.py          # Financial coaching
│   └── shopper_agent.py        # Personal shopping
├── api/
│   ├── __init__.py
│   ├── auth.py                  # Authentication endpoints ⭐ CRITICAL
│   ├── portfolio.py             # Portfolio management API ⭐ CRITICAL
│   ├── agents.py               # Agent interaction API
│   ├── analytics.py            # Financial analytics API
│   └── admin.py                # Administrative functions
├── utils/
│   ├── __init__.py
│   ├── encryption.py           # Data encryption ⭐ CRITICAL
│   ├── validators.py           # Input validation
│   ├── formatters.py           # Data formatting
│   ├── exceptions.py           # Custom exceptions
│   └── external_apis.py        # External API clients
└── tasks/
    ├── __init__.py
    ├── portfolio_tasks.py       # Portfolio calculations
    ├── data_sync_tasks.py      # Data synchronization
    └── agent_tasks.py          # Agent processing
```

## 🔧 Key Implementation Requirements

### Financial Accuracy Standards
- Use `Decimal` type for all monetary calculations (NEVER float)
- Portfolio values must reconcile to the penny
- CAPM calculations must follow academic formulas exactly
- All risk metrics must be mathematically sound

### Security Requirements
- Encrypt all sensitive financial data
- JWT authentication with proper token management
- Input validation on all endpoints
- Audit logging for all financial operations

### Performance Requirements
- Dashboard load: <2 seconds
- Portfolio calculations: <5 seconds
- Agent analysis: <30 seconds
- Database queries optimized with proper indexing

### Testing Requirements
- Property-based tests for financial correctness
- Unit tests for all business logic
- Integration tests for API endpoints
- 90%+ code coverage

## 📊 Sample Portfolio Data Structure

```python
SAMPLE_PORTFOLIO = {
    "user_id": "demo-user-123",
    "total_assets": 5102874.00,
    "total_liabilities": 1797683.00,
    "net_worth": 6900557.00,
    "assets": [
        {
            "type": "cash",
            "amount": 131196.00,
            "accounts": ["checking", "savings"]
        },
        {
            "type": "investments",
            "amount": 2643196.00,
            "breakdown": {
                "brokerage": 457291.00,
                "retirement_401k": 1500000.00,
                "retirement_ira": 610265.00,
                "education_529": 75640.00
            }
        },
        {
            "type": "real_estate",
            "amount": 1797683.00,
            "properties": [
                {
                    "address": "4912 Riverbend Drive",
                    "type": "primary",
                    "value": 803773.00
                },
                {
                    "address": "3623 Tupelo Place", 
                    "type": "rental",
                    "value": 474372.00
                }
            ]
        },
        {
            "type": "startup_equity",
            "amount": 450000.00,
            "companies": ["Confidencial", "Tangram Flex", "Polco", "Wilder"]
        }
    ]
}
```

## 🤖 Agent Implementation Pattern

Each agent should follow this pattern:

```python
class SpecializedAgent(BaseAgent):
    def __init__(self, user_id: str, portfolio_data: Dict[str, Any]):
        super().__init__(user_id, portfolio_data)
        self.specialty_service = SpecialtyService()
    
    def analyze(self) -> AgentResponse:
        # 1. Validate input data
        # 2. Perform specialized analysis
        # 3. Generate recommendations
        # 4. Calculate confidence score
        # 5. Return structured response
        
    def get_recommendations(self) -> List[Dict[str, Any]]:
        # Generate specific recommendations based on analysis
        
    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        # Calculate confidence based on data quality and analysis factors
```

## 🧪 Property-Based Test Examples

```python
# Portfolio Sum Property
@given(st.lists(st.floats(min_value=0, max_value=1000000), min_size=1))
def test_portfolio_sum_property(asset_values):
    total = sum(asset_values)
    calculated_total = portfolio_service.calculate_total(asset_values)
    assert abs(total - calculated_total) < 0.01

# CAPM Beta Bounds Property  
@given(st.floats(min_value=-2.0, max_value=3.0))
def test_capm_beta_bounds(beta):
    expected_return = camp_service.calculate_expected_return(beta)
    assert -0.5 <= expected_return <= 0.5
```

## 🚀 Development Workflow

1. **Start with Foundation**: Build Flask app, models, and auth first
2. **Add Core Services**: Portfolio, CAPM, and risk services
3. **Implement Agents**: Start with CFA, then CFP, then others
4. **Add APIs**: RESTful endpoints for all functionality
5. **Write Tests**: Property-based tests for financial accuracy
6. **Optimize Performance**: Caching, indexing, async processing

## 🔍 Code Quality Standards

- Follow PEP 8 style guidelines
- Use type hints throughout
- Comprehensive docstrings for all functions
- Error handling with proper logging
- Input validation on all user inputs
- Security-first approach for financial data

## 📈 Success Metrics

- All financial calculations accurate to 6 decimal places
- Portfolio reconciliation matches manual verification
- Agent recommendations show measurable improvements
- System handles 1000+ concurrent users
- 99.9% uptime with <2 second response times
- Zero critical security vulnerabilities

## 🎯 Claude Code Focus Areas

1. **Mathematical Accuracy**: Ensure all financial formulas are correct
2. **Data Security**: Proper encryption and authentication
3. **Performance**: Optimize for speed and scalability
4. **Testing**: Comprehensive test coverage with property-based tests
5. **Documentation**: Clear code documentation and API specs

Build this systematically, focusing on accuracy and security at every step. The financial calculations must be perfect - people's wealth depends on it!