#!/bin/bash

# Quick test script for dependency updates
echo "🔄 Quick update to dependency test branch..."

cd ~/PDF2UBL || { echo "❌ PDF2UBL directory not found"; exit 1; }

# Fetch and checkout test branch
git fetch origin
git checkout feature/dependency-updates
git pull origin feature/dependency-updates

# Update dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt 2>/dev/null || {
    echo "⚠️ Normal pip install failed, trying with --break-system-packages..."
    pip3 install -r requirements.txt --break-system-packages
}

# Build frontend if Node.js available
if command -v npm &> /dev/null; then
    echo "📦 Building frontend..."
    cd src/pdf2ubl/gui/frontend
    npm ci && npm run build
    cd ../../../..
fi

echo "✅ Ready to test! Start with:"
echo "python3 -m src.pdf2ubl.cli gui --host 0.0.0.0 --port 8000"