#!/bin/bash
# Start the Family Office Platform in development mode

set -e

echo "🚀 Starting Family Office Platform"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Redis is running
echo "📊 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠ Redis not running. Starting...${NC}"
    brew services start redis
    sleep 2
fi

# Check if PostgreSQL is running
echo ""
echo "🗄️  Checking PostgreSQL..."
if pg_isready > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
    echo "Start it with: brew services start postgresql@14"
    exit 1
fi

# Check if port 5001 is available
echo ""
echo "🔌 Checking port 5001..."
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port 5001 is in use${NC}"
    read -p "Kill existing process and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:5001 | xargs kill -9
        sleep 1
    else
        exit 1
    fi
fi

# Activate virtual environment
echo ""
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Export environment variables
export FLASK_APP=run.py
export FLASK_DEBUG=1

# Start Flask application
echo ""
echo -e "${GREEN}✓ Starting Flask application on http://localhost:5001${NC}"
echo ""
echo "=================================="
echo "  Family Office Platform Ready!"
echo "=================================="
echo ""
echo "  URL: http://localhost:5001"
echo "  Health: http://localhost:5001/health"
echo ""
echo "  Demo Account:"
echo "    Email: demo@familyoffice.com"
echo "    Password: DemoPassword123!"
echo ""
echo "  Press CTRL+C to stop"
echo ""

# Start Flask in foreground
flask run --host=0.0.0.0 --port=5001
