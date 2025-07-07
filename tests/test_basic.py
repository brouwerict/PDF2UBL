"""Basic tests for PDF2UBL."""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_import_modules():
    """Test that main modules can be imported."""
    import src.pdf2ubl.cli
    import src.pdf2ubl.extractors.pdf_extractor
    import src.pdf2ubl.templates.template_manager
    import src.pdf2ubl.exporters.ubl_exporter
    assert True


def test_template_loading():
    """Test that templates can be loaded."""
    from src.pdf2ubl.templates.template_manager import TemplateManager
    
    tm = TemplateManager()
    templates = tm.list_templates()
    
    assert len(templates) > 0
    assert any(t['template_id'] == 'generic_nl' for t in templates)
    assert any(t['template_id'] == 'dustin_nl' for t in templates)


def test_template_structure():
    """Test that templates have required fields."""
    from src.pdf2ubl.templates.template_manager import TemplateManager
    
    tm = TemplateManager()
    template = tm.get_template('generic_nl')
    
    assert template is not None
    assert hasattr(template, 'template_id')
    assert hasattr(template, 'name')
    assert hasattr(template, 'extraction_rules')


def test_pdf_extractor_initialization():
    """Test PDF extractor can be initialized."""
    from src.pdf2ubl.extractors.pdf_extractor import PDFExtractor
    
    extractor = PDFExtractor()
    assert extractor is not None


def test_ubl_exporter_initialization():
    """Test UBL exporter can be initialized."""
    from src.pdf2ubl.exporters.ubl_exporter import UBLExporter
    
    exporter = UBLExporter()
    assert exporter is not None


def test_cli_commands():
    """Test that CLI commands are defined."""
    from src.pdf2ubl.cli import app
    from typer.testing import CliRunner
    
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    
    assert result.exit_code == 0
    assert "convert" in result.stdout
    assert "extract" in result.stdout
    assert "template" in result.stdout