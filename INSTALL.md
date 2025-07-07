# Installation Guide for PDF2UBL

This guide provides detailed installation instructions for PDF2UBL on different platforms.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Node.js 16+ and npm (for web interface)
- Git

## Quick Installation (Recommended)

```bash
git clone https://github.com/brouwerict/PDF2UBL.git
cd PDF2UBL
./setup.sh
```

The setup script will:
1. Create a Python virtual environment
2. Install all Python dependencies
3. Build the React frontend (if Node.js is available)
4. Provide instructions for starting the application

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git nodejs npm

# Optional: Install OCR support
sudo apt install -y tesseract-ocr tesseract-ocr-nld

# Clone and setup
git clone https://github.com/brouwerict/PDF2UBL.git
cd PDF2UBL
./setup.sh
```

### macOS

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 node git

# Optional: Install OCR support
brew install tesseract tesseract-lang

# Clone and setup
git clone https://github.com/brouwerict/PDF2UBL.git
cd PDF2UBL
./setup.sh
```

### Windows

1. Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Install Node.js from [nodejs.org](https://nodejs.org/)
3. Install Git from [git-scm.com](https://git-scm.com/download/win)

```powershell
# Clone repository
git clone https://github.com/brouwerict/PDF2UBL.git
cd PDF2UBL

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Build frontend
cd src\pdf2ubl\gui\frontend
npm install
npm run build
cd ..\..\..\..
```

## Manual Installation Steps

### 1. Python Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd src/pdf2ubl/gui/frontend

# Install Node.js dependencies
npm install

# Build the React application
npm run build

# Return to project root
cd ../../../..
```

### 3. Verify Installation

```bash
# Test CLI
python3 -m src.pdf2ubl.cli --help

# Test import
python3 verify_installation.py
```

## Docker Installation

If you prefer using Docker:

```bash
# Build image
docker build -t pdf2ubl .

# Run container
docker run -p 8000:8000 pdf2ubl
```

## Troubleshooting

### Frontend Not Built Error

If you see "The React frontend is not built yet":

```bash
cd src/pdf2ubl/gui/frontend
npm install
npm run build
```

### Node.js Not Found

Install Node.js for your platform:
- Ubuntu/Debian: `sudo apt install nodejs npm`
- macOS: `brew install node`
- Windows: Download from [nodejs.org](https://nodejs.org/)

### Python Module Not Found

Make sure you've activated the virtual environment:
```bash
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### Permission Denied

Make the setup script executable:
```bash
chmod +x setup.sh
```

## Development Setup

For development, install additional dependencies:

```bash
pip install -r requirements-dev.txt
```

This includes testing tools, linters, and documentation generators.

## Next Steps

After installation:

1. Start the web interface:
   ```bash
   # For local access only
   python3 -m src.pdf2ubl.cli gui
   
   # For network access (access from other devices)
   python3 -m src.pdf2ubl.cli gui --host 0.0.0.0 --port 8000
   ```

2. Open your browser to:
   - Local: http://localhost:8000
   - Network: http://[your-server-ip]:8000

3. Or use the CLI directly:
   ```bash
   python3 -m src.pdf2ubl.cli convert invoice.pdf -o output.xml
   ```

See the [README](README.md) for more usage examples.