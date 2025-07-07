"""Smoke tests - basic functionality that should always work."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_python_environment():
    """Test that Python environment is working."""
    assert sys.version_info >= (3, 9)
    assert sys.path is not None


def test_project_structure():
    """Test that project files exist."""
    project_root = Path(__file__).parent.parent
    
    # Check key directories exist
    assert (project_root / "src").exists()
    assert (project_root / "src" / "pdf2ubl").exists()
    assert (project_root / "templates").exists()
    
    # Check key files exist
    assert (project_root / "requirements.txt").exists()
    assert (project_root / "README.md").exists()


def test_basic_imports():
    """Test basic Python imports work."""
    import json
    import pathlib
    import decimal
    import datetime
    
    assert json is not None
    assert pathlib is not None
    assert decimal is not None
    assert datetime is not None


def test_src_directory_accessible():
    """Test that src directory is accessible."""
    try:
        import src
        assert True
    except ImportError:
        # This is expected if src is not in PYTHONPATH yet
        project_root = Path(__file__).parent.parent
        src_path = project_root / "src"
        assert src_path.exists()


def test_pdf2ubl_package_structure():
    """Test PDF2UBL package structure exists."""
    project_root = Path(__file__).parent.parent
    pdf2ubl_path = project_root / "src" / "pdf2ubl"
    
    assert pdf2ubl_path.exists()
    assert (pdf2ubl_path / "cli.py").exists()
    assert (pdf2ubl_path / "extractors").exists()
    assert (pdf2ubl_path / "templates").exists()
    assert (pdf2ubl_path / "exporters").exists()


def test_templates_directory():
    """Test templates directory structure."""
    project_root = Path(__file__).parent.parent
    templates_path = project_root / "templates"
    
    assert templates_path.exists()
    assert templates_path.is_dir()
    
    # Check for at least one template file
    template_files = list(templates_path.glob("*.json"))
    assert len(template_files) > 0, "No template files found"


def test_simple_math():
    """Simple test that should always pass."""
    assert 2 + 2 == 4
    assert 10 > 5
    assert "test" == "test"


def test_file_operations():
    """Test basic file operations work."""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    # Read it back
    with open(temp_path, 'r') as f:
        content = f.read()
    
    assert content == "test content"
    
    # Clean up
    os.unlink(temp_path)