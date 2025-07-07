# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF2UBL is a Python application that converts PDF invoices to UBL (Universal Business Language) XML format. It features intelligent template-based extraction optimized for Dutch suppliers and accounting software like Hostfact. The system uses supplier-specific templates with automatic detection to ensure accurate data extraction from various invoice formats.

## Architecture

The codebase follows a modular, layered architecture:

- **CLI Interface** (`src/pdf2ubl/cli.py`): Rich command-line interface using Click/Typer with progress indicators
- **PDF Extraction** (`src/pdf2ubl/extractors/`): Multi-method PDF parsing (pdfplumber, PyMuPDF, OCR fallback)
- **Template System** (`src/pdf2ubl/templates/`): Supplier-specific pattern matching with automatic detection
- **UBL Export** (`src/pdf2ubl/exporters/`): UBL 2.1 compliant XML generation
- **Template Storage** (`templates/`): JSON-based supplier templates (123accu, DectDirect, Dustin, etc.)

### Key Components

1. **TemplateEngine**: Applies supplier-specific extraction rules with confidence scoring
2. **TemplateManager**: Handles template loading, detection, and fallback logic
3. **PDFExtractor**: Multi-method text extraction with positioning and table detection
4. **UBLExporter**: Generates valid UBL XML with proper VAT calculations and compliance
5. **CLI**: User-friendly interface with colored output and progress tracking

## Common Commands

### Core Operations
```bash
# Convert single PDF to UBL XML
python3 -m src.pdf2ubl.cli convert invoice.pdf -o output.xml

# Extract and preview data without generating XML
python3 -m src.pdf2ubl.cli extract invoice.pdf

# Batch convert multiple PDFs
python3 -m src.pdf2ubl.cli batch pdf_directory/ -o xml_output/

# Generate test UBL invoice for validation
python3 -m src.pdf2ubl.cli test -o test_invoice.xml
```

### Template Management
```bash
# List all available templates
python3 -m src.pdf2ubl.cli template list

# Create new supplier template
python3 -m src.pdf2ubl.cli template create supplier_id "Supplier Name" --supplier "Supplier B.V."

# Delete template
python3 -m src.pdf2ubl.cli template delete template_id

# View template usage statistics
python3 -m src.pdf2ubl.cli template stats
```

### Development and Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run with verbose logging
python3 -m src.pdf2ubl.cli convert invoice.pdf --verbose

# Test specific template
python3 -m src.pdf2ubl.cli convert invoice.pdf -t dustin_nl

# Extract with supplier hint for auto-detection
python3 -m src.pdf2ubl.cli convert invoice.pdf -s "DustinNederland"
```

## Template System

Templates are JSON files in the `templates/` directory that define supplier-specific extraction patterns. Each template includes:

- **Supplier Detection**: Patterns to identify the correct template
- **Field Extraction Rules**: Regex patterns for invoice numbers, amounts, dates
- **Line Item Processing**: Supplier-specific formatting and VAT calculations
- **Confidence Scoring**: Quality metrics for extraction accuracy

### Built-in Templates

The system includes optimized templates for Dutch suppliers:
- `123accu_nl.json` - 123accu B.V. invoices
- `dustin_nl.json` - Dustin Nederland B.V.
- `dectdirect_nl.json` - DectDirect.NL
- `proserve_nl.json` - Proserve B.V.
- `nextname_nl.json` - NextName B.V.
- `opslagruimte_nl.json` - Opslagruimte Haaksbergen
- `weservit_nl.json` - WeServit Cloud
- `generic_nl.json` - Fallback for unknown suppliers

### Template Structure

Templates use structured extraction rules with pattern matching:
```json
{
  "template_id": "supplier_nl",
  "name": "Supplier Name",
  "supplier_patterns": [/* detection patterns */],
  "extraction_rules": [/* field extraction */],
  "table_rules": [/* line item processing */]
}
```

## UBL Output Format

Generates UBL 2.1 compliant XML with:
- **Proper VAT calculations**: VAT-exclusive line items with correct tax amounts
- **Complete party information**: Supplier and customer details
- **Line item accuracy**: Descriptions, quantities, unit prices
- **Payment terms**: IBAN support and payment conditions
- **Validation compliance**: Passes UBL schema validation

## Key Files and Locations

- **Main CLI**: `src/pdf2ubl/cli.py` - Command-line interface entry point
- **Template Engine**: `src/pdf2ubl/templates/template_engine.py` - Core extraction logic
- **Template Manager**: `src/pdf2ubl/templates/template_manager.py` - Template loading and detection
- **UBL Exporter**: `src/pdf2ubl/exporters/ubl_exporter.py` - XML generation
- **PDF Extractor**: `src/pdf2ubl/extractors/pdf_extractor.py` - Multi-method PDF parsing
- **Templates Directory**: `templates/` - Supplier-specific extraction templates
- **Test Files**: `tests/` - Sample PDFs for testing and validation

## Configuration

The system supports configuration via:
1. JSON config files (`pdf2ubl.json`, `hostfact_config.json`)
2. Environment variables (prefixed with `PDF2UBL_`)
3. Command-line options

Key settings include VAT rates, currency defaults, confidence thresholds, and OCR language preferences.

## Hostfact Integration

Special focus on Hostfact accounting software compatibility:
- Proper supplier name extraction (no "Unknown Supplier" errors)
- Correct VAT-exclusive pricing for line items
- Accurate total amount calculations
- UBL XML format compliance for seamless import