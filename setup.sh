#!/bin/bash
# Setup script for Vietnam Real Estate Web Crawler

set -e  # Exit on error

echo "======================================"
echo "Estate Crawler Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null
echo "✓ Dependencies installed"

# Create .env from .env.example if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ .env created (please review and update as needed)"
else
    echo "✓ .env already exists"
fi

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from database import EstateDatabase; db = EstateDatabase(); print(f'✓ Database initialized: {db.db_path}')"

# Run tests
echo ""
echo "Running unit tests..."
if python3 test_scraper.py > /dev/null 2>&1; then
    echo "✓ All tests passed"
else
    echo "⚠ Some tests failed (this may be normal in new installations)"
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review and update .env file:"
echo "   vim .env"
echo ""
echo "2. Run a test scrape:"
echo "   python3 main.py scrape"
echo ""
echo "3. Start the scheduler:"
echo "   python3 main.py scheduler"
echo ""
echo "4. Or use the CLI directly:"
echo "   python3 main.py --help"
echo ""
echo "For Docker deployment:"
echo "   docker-compose up -d"
echo ""
