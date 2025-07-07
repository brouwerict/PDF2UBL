#!/bin/bash
# Setup script for PDF2UBL

echo "==================================="
echo "PDF2UBL Setup Script"
echo "==================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Warning: Node.js is not installed. You need Node.js 16+ to build the frontend."
    echo "Install with: sudo apt install nodejs npm"
else
    echo "✓ Node.js $(node --version) found"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if npm is available and build frontend
if command -v npm &> /dev/null; then
    echo ""
    echo "Building React frontend..."
    cd src/pdf2ubl/gui/frontend
    
    # Install npm dependencies
    echo "Installing npm dependencies..."
    npm install
    
    # Build the frontend
    echo "Building frontend application..."
    npm run build
    
    if [ $? -eq 0 ]; then
        echo "✓ Frontend built successfully!"
    else
        echo "✗ Frontend build failed!"
        exit 1
    fi
    
    cd ../../../..
else
    echo ""
    echo "⚠️  IMPORTANT: Frontend not built!"
    echo "To build the frontend manually:"
    echo "  1. Install Node.js: sudo apt install nodejs npm"
    echo "  2. cd src/pdf2ubl/gui/frontend"
    echo "  3. npm install"
    echo "  4. npm run build"
fi

echo ""
echo "==================================="
echo "Setup complete!"
echo ""
echo "To start the application:"
echo "  1. source venv/bin/activate"
echo "  2. python3 -m src.pdf2ubl.cli gui"
echo ""
echo "The web interface will be available at: http://localhost:8000"
echo "==================================="