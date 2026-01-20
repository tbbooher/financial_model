# Development Environment Setup

## Quick Start

Your development environment is ready! Here's what's configured:

### ✅ What's Already Set Up

1. **Virtual Environment Auto-Activation**
   - Just `cd` into this directory and venv activates automatically
   - Uses `direnv` (configured in `.envrc`)

2. **Environment Variables**
   - Created `.env` with secure, generated keys
   - PostgreSQL detected and configured
   - Ready for local development

3. **Database Migrations**
   - Migration system initialized
   - Ready to create your databases

## Getting Started

### 1. Start Required Services

```bash
# Start Redis (required for Celery background tasks)
brew services start redis

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 2. Set Up Database

```bash
# Create PostgreSQL databases
createdb family_office_dev
createdb family_office_test

# Apply migrations
flask db upgrade
```

**Or use the automated setup script:**

```bash
./setup_dev.sh
```

### 3. Create Demo Data (Optional)

```bash
# Run the app once to trigger demo data creation
python run.py

# Or create demo data manually
flask shell
>>> from run import create_demo_data
>>> create_demo_data()
```

### 4. Run the Application

```bash
# Development server
flask run

# Or with auto-reload
FLASK_DEBUG=1 flask run

# Visit: http://localhost:5000
```

## Environment Configuration

Your `.env` file is configured with:

### ✅ Generated & Ready
- `SECRET_KEY` - Secure Flask secret
- `JWT_SECRET_KEY` - JWT token signing
- `ENCRYPTION_KEY` - Data encryption
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection

### ⚠️ Optional (Add as needed)
- `ALPHA_VANTAGE_API_KEY` - Stock market data (free at https://www.alphavantage.co/support/#api-key)
- `PLAID_CLIENT_ID` / `PLAID_SECRET` - Banking integration (free sandbox at https://plaid.com/docs/quickstart/)
- Email settings - For notifications (optional in development)

## Running Background Tasks

The platform uses Celery for background processing:

```bash
# Start Celery worker (in separate terminal)
celery -A app.celery worker --loglevel=info

# For development with auto-reload
watchmedo auto-restart -d . -p '*.py' -- celery -A app.celery worker --loglevel=info
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_models.py

# Run with verbose output
pytest -v
```

## Common Tasks

### Database Management

```bash
# Create a new migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback one migration
flask db downgrade

# See migration history
flask db history
```

### Check System Health

```bash
# Health check endpoint
curl http://localhost:5000/health

# Admin stats (requires authentication)
curl http://localhost:5000/api/v1/admin/stats
```

### Flask Shell

```bash
# Interactive Python shell with app context
flask shell

# Then you can interact with models:
>>> from app.models import User, Asset
>>> users = User.query.all()
>>> print(users)
```

## Directory Structure

```
booher_family_office/
├── .env                 # Your local environment variables (not in git)
├── .envrc              # Auto-activates venv with direnv
├── setup_dev.sh        # Automated setup script
├── migrations/         # Database migrations
│   └── versions/       # Migration files
├── app/                # Application code
│   ├── models/         # Database models
│   ├── api/           # REST API endpoints
│   ├── agents/        # AI agent implementations
│   ├── services/      # Business logic
│   └── tasks/         # Celery background tasks
├── tests/             # Test suite
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── property/      # Property-based tests
└── venv/              # Virtual environment (auto-activated)
```

## Troubleshooting

### Virtual environment not activating

```bash
# Make sure direnv is working
direnv allow .

# Test it
cd ..
cd booher_family_office
# Should see: direnv: loading .envrc
```

### Database connection errors

```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql -l | grep family_office

# Recreate if needed
dropdb family_office_dev
createdb family_office_dev
flask db upgrade
```

### Redis connection errors

```bash
# Check Redis is running
redis-cli ping

# Start if needed
brew services start redis

# Check connection
redis-cli
> PING
> exit
```

### Import errors

```bash
# Make sure you're in venv
which python
# Should show: /Users/tim/code/booher_family_office/venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

1. ✅ Start Redis: `brew services start redis`
2. ✅ Create databases: `./setup_dev.sh` or manual setup
3. ✅ Run migrations: `flask db upgrade`
4. ✅ Start the app: `flask run`
5. ✅ Run tests: `pytest`

## Demo Credentials

If you ran the demo data creation:

- **Email:** demo@familyoffice.local
- **Password:** DemoPassword123!

## API Documentation

Once running, the API is available at:

- Health Check: `GET http://localhost:5000/health`
- Portfolio: `GET http://localhost:5000/api/v1/portfolio/summary`
- Authentication: `POST http://localhost:5000/api/v1/auth/login`

See `CLAUDE.md` for full API documentation and development guide.

## Getting API Keys (Optional)

### Alpha Vantage (Stock Data)
1. Visit: https://www.alphavantage.co/support/#api-key
2. Free tier: 5 API calls per minute, 500 per day
3. Add to `.env`: `ALPHA_VANTAGE_API_KEY=your_key`

### Plaid (Banking Integration)
1. Visit: https://dashboard.plaid.com/signup
2. Free sandbox environment
3. Add to `.env`:
   ```
   PLAID_CLIENT_ID=your_client_id
   PLAID_SECRET=your_secret
   PLAID_ENV=sandbox
   ```

## Support

- Check `CLAUDE.md` for comprehensive development guide
- Check `migrations/MIGRATION_GUIDE.md` for database migration help
- Run tests to ensure everything works: `pytest`
