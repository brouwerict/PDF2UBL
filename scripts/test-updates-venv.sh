#!/bin/bash

# Test script using virtual environment for Ubuntu servers
echo "🔄 Testing dependency updates with virtual environment..."

cd ~/PDF2UBL || { echo "❌ PDF2UBL directory not found"; exit 1; }

# Fetch and checkout test branch
git fetch origin
git checkout feature/dependency-updates
git pull origin feature/dependency-updates

# Create and activate virtual environment
echo "🐍 Setting up virtual environment..."
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Install dependencies in virtual environment
echo "📦 Installing dependencies in virtual environment..."
pip install --upgrade pip
pip install -r requirements.txt

# Build frontend if Node.js available
if command -v npm &> /dev/null; then
    echo "📦 Building frontend..."
    cd src/pdf2ubl/gui/frontend
    npm ci && npm run build
    cd ../../../..
fi

# Test basic imports
echo "🧪 Testing basic imports..."
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python3 -c "import src.pdf2ubl.cli; print('✅ CLI import successful')" || echo "❌ CLI import failed"
python3 -c "import src.pdf2ubl.gui.app; print('✅ GUI import successful')" || echo "❌ GUI import failed"

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To start the GUI, run:"
echo "source venv/bin/activate"
echo "python3 -m src.pdf2ubl.cli gui --host 0.0.0.0 --port 8000"