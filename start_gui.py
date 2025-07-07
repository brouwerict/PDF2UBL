#!/usr/bin/env python3
"""Startup script for PDF2UBL GUI."""

import sys
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def start_backend():
    """Start the FastAPI backend server."""
    import uvicorn
    from src.pdf2ubl.gui.web.main import app
    
    print("🚀 Starting PDF2UBL GUI Backend...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

def check_frontend():
    """Check if frontend is built and provide instructions."""
    frontend_dir = Path("src/pdf2ubl/gui/frontend")
    build_dir = frontend_dir / "build"
    
    if not build_dir.exists():
        print("\n📦 Frontend not built yet. To build the React frontend:")
        print(f"1. cd {frontend_dir}")
        print("2. npm install")
        print("3. npm run build")
        print("\nFor development:")
        print("4. npm start (runs on http://localhost:3000)")
        print("\nThe backend API will be available at http://localhost:8000")
        print("API documentation: http://localhost:8000/api/docs")
    else:
        print("✅ Frontend is built and will be served at http://localhost:8000")

def main():
    """Main function."""
    setup_logging()
    
    print("="*60)
    print("🎯 PDF2UBL GUI - Web Interface")
    print("="*60)
    
    # Check frontend status
    check_frontend()
    
    print("\n🔧 Available endpoints:")
    print("- Main interface: http://localhost:8000")
    print("- API docs (Swagger): http://localhost:8000/api/docs")
    print("- API docs (ReDoc): http://localhost:8000/api/redoc")
    print("- Health check: http://localhost:8000/health")
    
    print("\n💡 Features:")
    print("- PDF to UBL XML conversion")
    print("- Template management")
    print("- ML-powered template generation")
    print("- Batch processing")
    print("- Real-time progress tracking")
    
    print("\n🚀 Starting backend server...")
    print("Press Ctrl+C to stop")
    print("-"*60)
    
    try:
        start_backend()
    except KeyboardInterrupt:
        print("\n👋 Shutting down PDF2UBL GUI...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()