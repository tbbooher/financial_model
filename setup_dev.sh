#!/bin/bash
# Development Environment Setup Script
# Run this after creating your .env file

set -e

echo "🚀 Family Office Platform - Development Setup"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create .env file first (copy from .env.example)"
    exit 1
fi

echo -e "${GREEN}✓ .env file found${NC}"

# Check PostgreSQL
echo ""
echo "📊 Checking PostgreSQL..."
if pg_isready > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"

    # Create databases
    echo "Creating databases..."
    createdb family_office_dev 2>/dev/null && echo -e "${GREEN}✓ Created family_office_dev${NC}" || echo -e "${YELLOW}⚠ Database family_office_dev already exists${NC}"
    createdb family_office_test 2>/dev/null && echo -e "${GREEN}✓ Created family_office_test${NC}" || echo -e "${YELLOW}⚠ Database family_office_test already exists${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
    echo "Start it with: brew services start postgresql@14"
    echo "Or use SQLite by updating DATABASE_URL in .env"
fi

# Check Redis
echo ""
echo "🔴 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠ Redis is not running${NC}"
    echo "Start it with: brew services start redis"
    echo "Or use Docker: docker run -d -p 6379:6379 redis:alpine"
fi

# Check virtual environment
echo ""
echo "🐍 Checking Python virtual environment..."
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"

    # Activate and check dependencies
    source venv/bin/activate
    echo "Checking Python version..."
    python --version

    echo ""
    echo "Installing/updating dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Create it with: python3 -m venv venv"
    exit 1
fi

# Run database migrations
echo ""
echo "📦 Setting up database schema..."
if [ -d "migrations" ]; then
    export FLASK_APP=run.py
    flask db upgrade && echo -e "${GREEN}✓ Database migrations applied${NC}" || echo -e "${YELLOW}⚠ Migration failed - database may need to be created first${NC}"
else
    echo -e "${YELLOW}⚠ No migrations folder found${NC}"
fi

# Create demo data (optional)
echo ""
read -p "Create demo user and sample data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python run.py create-demo-data && echo -e "${GREEN}✓ Demo data created${NC}" || echo -e "${YELLOW}⚠ Demo data creation failed${NC}"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start Redis: brew services start redis"
echo "  2. Run the app: flask run"
echo "  3. Visit: http://localhost:5000"
echo ""
echo "Demo user credentials (if created):"
echo "  Email: demo@familyoffice.local"
echo "  Password: DemoPassword123!"
echo ""
