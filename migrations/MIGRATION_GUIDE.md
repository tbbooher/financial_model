# Database Migrations Guide

This folder contains Alembic/Flask-Migrate database migrations for the Family Office Platform.

## Quick Start

### Initialize Database (First Time)
```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export FLASK_APP=run.py
export DATABASE_URL="your_database_url"

# Apply all migrations
flask db upgrade
```

### Creating New Migrations

When you make changes to the models, create a new migration:

```bash
# Generate migration based on model changes
flask db migrate -m "Description of changes"

# Review the generated migration file in migrations/versions/
# Then apply the migration
flask db upgrade
```

### Common Commands

```bash
# Show current migration status
flask db current

# Show migration history
flask db history

# Upgrade to latest migration
flask db upgrade

# Upgrade to specific migration
flask db upgrade <revision_id>

# Downgrade one migration
flask db downgrade

# Downgrade to specific migration
flask db downgrade <revision_id>

# Show SQL without executing
flask db upgrade --sql
```

## Migration Files

### Initial Migration
- `ca3d44803198_initial_migration_with_all_models.py` - Creates all core tables:
  - **users** - User accounts and authentication
  - **accounts** - Financial accounts (brokerage, retirement, bank, etc.)
  - **assets** - Investment holdings (stocks, bonds, ETFs, etc.)
  - **real_estate** - Real estate property holdings
  - **transactions** - Financial transactions (buy, sell, dividend, etc.)
  - **agent_tasks** - AI agent analysis tasks and results

## Database Schema

### Core Tables

1. **users** - User management
   - Authentication (email, password)
   - Profile (name, risk tolerance)
   - Financial overview (net worth)
   - MFA settings

2. **accounts** - Account tracking
   - Multiple account types
   - Plaid integration support
   - Sync status tracking

3. **assets** - Investment holdings
   - Stock, bond, ETF tracking
   - Cost basis and current value
   - Performance metrics (beta, alpha, returns)

4. **real_estate** - Property management
   - Property details and valuation
   - Rental income tracking
   - Mortgage information

5. **transactions** - Transaction history
   - Buy/sell/dividend transactions
   - Realized gains tracking
   - Account reconciliation

6. **agent_tasks** - AI agent system
   - Task scheduling and tracking
   - Analysis results storage
   - Retry logic support

## Best Practices

1. **Always review generated migrations** before applying them
2. **Test migrations** in development before production
3. **Backup database** before running migrations in production
4. **Version control** all migration files
5. **Don't modify** existing migration files after they've been applied
6. **Create new migrations** for schema changes instead

## Database Setup for Different Environments

### Development (SQLite)
```bash
export DATABASE_URL="sqlite:///family_office_dev.db"
flask db upgrade
```

### Development (PostgreSQL)
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/family_office_dev"
flask db upgrade
```

### Testing
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/family_office_test"
flask db upgrade
```

### Production
```bash
# Use production database URL from environment
flask db upgrade
```

## Troubleshooting

### Migration fails with "Target database is not up to date"
```bash
# Check current migration
flask db current

# Force stamp to specific version (use with caution)
flask db stamp <revision_id>
```

### Need to undo a migration
```bash
# Downgrade one step
flask db downgrade

# Or downgrade to specific revision
flask db downgrade <revision_id>
```

### Database out of sync with migrations
```bash
# Check what Alembic thinks is current
flask db current

# Check actual database state and compare with migrations
flask db history
```

## Notes

- This project uses Flask-Migrate (wrapper around Alembic)
- Migrations are database-agnostic but tested with PostgreSQL
- UUID primary keys are used for all tables
- All timestamps use timezone-aware datetime (timezone.utc)
- Indexes are created for common query patterns
