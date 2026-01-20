# Running the Family Office Platform

## Quick Start

The app is **CURRENTLY RUNNING** at: http://localhost:5001

### Start/Restart the App

```bash
./start_dev.sh
```

This script will:
- ✓ Check Redis and PostgreSQL are running
- ✓ Activate the virtual environment
- ✓ Start Flask in debug mode on port 5001

### Manual Start

```bash
# Activate virtual environment (auto-activated when you cd into directory)
source venv/bin/activate

# Start Flask
export FLASK_APP=run.py
flask run --port=5001
```

## Current Status

✅ **Services Running:**
- Redis (port 6379)
- PostgreSQL (with `family_office_dev` database)
- Flask App (port 5001)

✅ **Database Setup:**
- ✓ Migrations applied
- ✓ 6 tables created (users, accounts, assets, real_estate, transactions, agent_tasks)
- ✓ Demo user created

## Demo Account

**Email:** `demo@familyoffice.com`
**Password:** `DemoPassword123!`

## Available Endpoints

### Health Check
```bash
curl http://localhost:5001/health
```

### Admin Status
```bash
curl http://localhost:5001/api/v1/admin/stats
```

### Authentication
```bash
# Login
curl -X POST http://localhost:5001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@familyoffice.com","password":"DemoPassword123!"}'

# Register
curl -X POST http://localhost:5001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!","first_name":"Test","last_name":"User"}'
```

### Portfolio (requires authentication)
```bash
# Get portfolio summary (replace TOKEN with your JWT)
curl http://localhost:5001/api/v1/portfolio/summary \
  -H "Authorization: Bearer TOKEN"
```

## Database Access

```bash
# Connect to database
psql family_office_dev

# Useful queries
psql family_office_dev -c "SELECT * FROM users;"
psql family_office_dev -c "SELECT * FROM accounts;"
psql family_office_dev -c "SELECT * FROM assets;"
```

## Running Background Tasks

For full functionality, start a Celery worker:

```bash
# In a separate terminal
celery -A app.celery worker --loglevel=info
```

This enables:
- Portfolio value updates
- Agent analysis tasks
- Data synchronization

## Stopping the App

```bash
# Find and kill Flask process
lsof -ti:5001 | xargs kill

# Or use CTRL+C if running in foreground
```

## Logs

```bash
# View Flask logs (if running in background)
tail -f /tmp/flask_output.log

# View application logs
tail -f logs/family_office.log
```

## Troubleshooting

### Port 5000 in use
Port 5000 conflicts with macOS AirPlay. The app runs on port 5001 instead.

### Database connection errors
```bash
# Verify PostgreSQL is running
pg_isready

# Check database exists
psql -l | grep family_office
```

### Redis connection errors
```bash
# Check Redis is running
redis-cli ping

# Start Redis
brew services start redis
```

### Module import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## Development Workflow

1. **Make code changes** - Auto-reload is enabled in debug mode
2. **Test changes** - `pytest` or `pytest tests/unit/`
3. **Database changes** - `flask db migrate -m "description"` then `flask db upgrade`
4. **View API docs** - See `CLAUDE.md` for full API documentation

## Useful Flask Commands

```bash
# Interactive shell
flask shell

# Database migrations
flask db migrate -m "Add new field"
flask db upgrade
flask db downgrade

# Custom commands
flask init-db    # Initialize database
flask seed-data  # Create demo data
```

## Next Steps

1. ✅ App is running - visit http://localhost:5001/health
2. 🔨 Fix login endpoint (currently returns 500)
3. 📊 Add sample portfolio data
4. 🧪 Run tests: `pytest`
5. 🤖 Start Celery worker for AI agents

## Full Documentation

- `DEV_SETUP.md` - Complete setup guide
- `CLAUDE.md` - Development guide and API documentation
- `migrations/MIGRATION_GUIDE.md` - Database migration guide
