#!/bin/bash

# Test script voor dependency updates op Ubuntu server
# Gebruik: ./test-dependency-updates.sh

echo "🧪 Testing PDF2UBL dependency updates on Ubuntu server"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "src/pdf2ubl" ]; then
    echo "❌ Error: Run this script from the PDF2UBL project root directory"
    exit 1
fi

# Switch to test branch
echo "📋 Switching to dependency updates branch..."
git fetch origin
git checkout feature/dependency-updates
git pull origin feature/dependency-updates

# Check Node.js availability
echo "🔍 Checking Node.js installation..."
if command -v node &> /dev/null; then
    echo "✅ Node.js found: $(node --version)"
    echo "✅ NPM found: $(npm --version)"
    
    # Install and build frontend
    echo "📦 Installing frontend dependencies..."
    cd src/pdf2ubl/gui/frontend
    npm ci
    
    echo "🏗️ Building frontend..."
    npm run build
    
    if [ $? -eq 0 ]; then
        echo "✅ Frontend build successful!"
    else
        echo "❌ Frontend build failed!"
        exit 1
    fi
    
    cd ../../../../
else
    echo "⚠️ Node.js not found - skipping frontend build"
    echo "   Frontend will use existing build or development mode"
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    # Try normal install first
    pip3 install -r requirements.txt 2>/dev/null || {
        echo "⚠️ Normal pip install failed, trying with --break-system-packages..."
        pip3 install -r requirements.txt --break-system-packages
    }
else
    echo "⚠️ pip3 not found, trying with apt packages..."
    sudo apt update
    sudo apt install -y python3-pip python3-pymupdf python3-lxml python3-pandas python3-numpy
fi

# Test basic functionality
echo "🧪 Testing basic imports..."
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python3 -c "import src.pdf2ubl.cli; print('✅ CLI import successful')"
python3 -c "import src.pdf2ubl.gui.app; print('✅ GUI import successful')"

# Start GUI for testing
echo ""
echo "🚀 Ready to start GUI for testing!"
echo ""
echo "Run the following command to start the GUI:"
echo "python3 -m src.pdf2ubl.cli gui --host 0.0.0.0 --port 8000"
echo ""
echo "Then test these features:"
echo "- ✅ PDF conversion (upload and convert)"
echo "- ✅ Template management (create/edit templates)"
echo "- ✅ ML features (analyze PDF and generate templates)"
echo "- ✅ Multi-file upload and batch processing"
echo ""
echo "If everything works, the dependency updates are safe to merge!"