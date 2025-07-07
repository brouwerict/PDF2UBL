#!/usr/bin/env python3
"""PDF2UBL - Main entry point for the application."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from pdf2ubl.cli import cli

if __name__ == "__main__":
    cli()