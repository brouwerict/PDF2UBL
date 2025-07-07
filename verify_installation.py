#!/usr/bin/env python3
"""Installation verification script for PDF2UBL."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    
    try:
        from pdf2ubl.extractors.pdf_extractor import PDFExtractor
        print("✓ PDF extractor import successful")
        
        from pdf2ubl.exporters.ubl_exporter import UBLExporter
        print("✓ UBL exporter import successful")
        
        from pdf2ubl.templates.template_manager import TemplateManager
        print("✓ Template manager import successful")
        
        from pdf2ubl.templates.template_engine import TemplateEngine
        print("✓ Template engine import successful")
        
        from pdf2ubl.utils.config import load_config
        print("✓ Configuration system import successful")
        
        from pdf2ubl.utils.validators import validate_ubl, validate_vat_number
        print("✓ Validators import successful")
        
        from pdf2ubl.utils.formatters import format_amount, format_date
        print("✓ Formatters import successful")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_core_functionality():
    """Test core functionality without requiring external PDFs."""
    print("\nTesting core functionality...")
    
    try:
        # Test UBL exporter
        from pdf2ubl.exporters.ubl_exporter import UBLExporter
        exporter = UBLExporter()
        test_invoice = exporter.create_test_invoice()
        xml_content = exporter.xml_generator.generate_xml(test_invoice)
        
        if len(xml_content) > 1000 and "Invoice" in xml_content:
            print("✓ UBL XML generation successful")
        else:
            print("✗ UBL XML generation failed")
            return False
        
        # Test XML validation
        is_valid = exporter.validate_ubl_xml(xml_content)
        if is_valid:
            print("✓ UBL XML validation successful")
        else:
            print("✗ UBL XML validation failed")
            return False
        
        # Test template manager
        from pdf2ubl.templates.template_manager import TemplateManager
        template_manager = TemplateManager(Path("templates"))
        templates = template_manager.get_templates()
        
        if len(templates) >= 3:  # We should have the default templates
            print(f"✓ Template system working ({len(templates)} templates loaded)")
        else:
            print(f"✗ Template system issue (only {len(templates)} templates)")
            return False
        
        # Test configuration
        from pdf2ubl.utils.config import load_config
        config = load_config()
        if config.default_currency == "EUR":
            print("✓ Configuration system working")
        else:
            print("✗ Configuration system failed")
            return False
        
        # Test validators
        from pdf2ubl.utils.validators import validate_vat_number, validate_iban
        vat_valid, _ = validate_vat_number("NL123456789B01", "NL")
        iban_valid, _ = validate_iban("NL91ABNA0417164300")
        
        if vat_valid and iban_valid:
            print("✓ Validation system working")
        else:
            print("✗ Validation system failed")
            return False
        
        # Test formatters
        from pdf2ubl.utils.formatters import format_amount, format_date
        from datetime import datetime
        
        formatted_amount = format_amount(1234.56, "EUR")
        formatted_date = format_date(datetime(2024, 1, 15))
        
        if "€" in formatted_amount and "15-01-2024" == formatted_date:
            print("✓ Formatting system working")
        else:
            print("✗ Formatting system failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Core functionality test failed: {e}")
        return False


def test_dependencies():
    """Test critical dependencies."""
    print("\nTesting dependencies...")
    
    try:
        import fitz  # PyMuPDF
        print("✓ PyMuPDF available")
        
        import pdfplumber
        print("✓ pdfplumber available")
        
        from lxml import etree
        print("✓ lxml available")
        
        import pandas as pd
        print("✓ pandas available")
        
        import click
        print("✓ click available")
        
        from rich.console import Console
        print("✓ rich available")
        
        return True
        
    except ImportError as e:
        print(f"✗ Dependency missing: {e}")
        return False


def main():
    """Run all verification tests."""
    print("PDF2UBL Installation Verification")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test dependencies
    if not test_dependencies():
        all_passed = False
    
    # Test core functionality
    if not test_core_functionality():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! PDF2UBL is correctly installed and ready to use.")
        print("\nNext steps:")
        print("1. Run: ./pdf2ubl.py template init  (if not already done)")
        print("2. Test with: ./pdf2ubl.py test")
        print("3. Convert a PDF: ./pdf2ubl.py convert your_invoice.pdf")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()