# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF2UBL is a comprehensive Python application that converts PDF invoices to UBL (Universal Business Language) XML format. It features intelligent template-based extraction, machine learning capabilities, and a modern web interface, optimized for Dutch suppliers and accounting software like Hostfact.

## Architecture

The codebase follows a modular, layered architecture:

### Core Components
- **CLI Interface** (`src/pdf2ubl/cli.py`): Click-based command-line interface with rich output
- **PDF Extraction** (`src/pdf2ubl/extractors/`): Multi-method PDF parsing (pdfplumber, PyMuPDF, OCR fallback)
- **Template System** (`src/pdf2ubl/templates/`): Supplier-specific pattern matching with confidence scoring
- **UBL Export** (`src/pdf2ubl/exporters/`): UBL 2.1 compliant XML generation
- **Machine Learning** (`src/pdf2ubl/ml/`): Auto template generation and pattern analysis
- **Web GUI** (`src/pdf2ubl/gui/`): React frontend with FastAPI backend
- **Template Storage** (`templates/`): JSON-based supplier templates (13 built-in templates)

### Key Architecture Files
- **Main Entry**: `pdf2ubl.py` - Convenience wrapper for CLI
- **CLI Core**: `src/pdf2ubl/cli.py` - Command-line interface implementation
- **Template Engine**: `src/pdf2ubl/templates/template_engine.py` - Core extraction logic
- **Template Manager**: `src/pdf2ubl/templates/template_manager.py` - Template loading and detection
- **UBL Exporter**: `src/pdf2ubl/exporters/ubl_exporter.py` - XML generation with VAT compliance
- **PDF Extractor**: `src/pdf2ubl/extractors/pdf_extractor.py` - Multi-method PDF parsing coordinator

## Common Commands

### Core Operations
```bash
# Convert single PDF to UBL XML
python3 -m src.pdf2ubl.cli convert invoice.pdf -o output.xml

# OR using convenience wrapper
./pdf2ubl.py convert invoice.pdf -o output.xml

# Extract and preview data without generating XML
python3 -m src.pdf2ubl.cli extract invoice.pdf

# Batch convert multiple PDFs
python3 -m src.pdf2ubl.cli batch pdf_directory/ -o xml_output/

# Generate test UBL invoice for validation
python3 -m src.pdf2ubl.cli test -o test_invoice.xml

# Start web GUI interface
python3 -m src.pdf2ubl.cli gui
# OR
python3 start_gui.py
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

# Activate virtual environment
source ./activate.sh

# Verify installation
python3 verify_installation.py

# Run comprehensive validation (95.7% success rate)
python3 validate_tests2_comprehensive.py

# Run with verbose logging
python3 -m src.pdf2ubl.cli convert invoice.pdf --verbose

# Test specific template
python3 -m src.pdf2ubl.cli convert invoice.pdf -t dustin_nl

# Extract with supplier hint for auto-detection
python3 -m src.pdf2ubl.cli convert invoice.pdf -s "DustinNederland"
```

## Template System

### Built-in Templates (13 total)
The system includes optimized templates for Dutch suppliers:
- `123accu_nl.json` - 123accu B.V. IT components
- `cheapconnect_nl.json` - CheapConnect telecommunication
- `coolblue_nl.json` - Coolblue online retail
- `dectdirect_nl.json` - DectDirect DECT telephony
- `dustin_nl.json` - Dustin Nederland IT hardware
- `fixxar_nl.json` - Fixxar technical services (OCR optimized)
- `fonu_nl.json` - Fonu telecommunication
- `nextname_nl.json` - NextName domains and hosting
- `opslagruimte_nl.json` - Storage services
- `proserve_nl.json` - Proserve cloud services
- `vdx_nl.json` - VDX telecommunication
- `weservit_nl.json` - WeServit cloud backup
- `generic_nl.json` - Fallback for unknown suppliers

### Template Structure
Templates are JSON files with structured extraction rules:
```json
{
  "template_id": "supplier_nl",
  "name": "Supplier Name",
  "supplier_patterns": [
    {
      "pattern": "Company Name Pattern",
      "confidence_threshold": 0.9,
      "priority": 10
    }
  ],
  "extraction_rules": [
    {
      "field_name": "invoice_number",
      "field_type": "text",
      "patterns": [
        {
          "pattern": "Invoice\\s*[:#]?\\s*(\\d+)",
          "confidence_threshold": 0.8
        }
      ]
    }
  ]
}
```

## Web GUI

### Frontend (React + TypeScript)
- **Location**: `src/pdf2ubl/gui/frontend/`
- **Key Files**:
  - `src/App.tsx` - Main application component
  - `src/pages/ConversionPage.tsx` - PDF conversion interface
  - `src/pages/TemplateEditor.tsx` - Template editing interface
  - `src/pages/MLPage.tsx` - Machine learning features
  - `src/services/api.ts` - API client

### Backend (FastAPI)
- **Location**: `src/pdf2ubl/gui/web/`
- **Key Files**:
  - `main.py` - FastAPI application
  - `../api/` - REST API endpoints

### GUI Features
- PDF upload and conversion
- Template management
- ML-powered template generation
- Real-time extraction preview
- Batch processing
- Conversion statistics

## Machine Learning Features

### Auto Template Generation
- **Location**: `src/pdf2ubl/ml/`
- **Key Components**:
  - `template_generator.py` - ML template creation
  - `pattern_analyzer.py` - Pattern recognition
  - `confidence_predictor.py` - Quality scoring

### ML Workflow
1. Upload PDF samples from new supplier
2. AI analyzes structure and patterns
3. Template generated with extraction rules
4. Validation and fine-tuning via GUI
5. Production deployment

## UBL Output Format

Generates UBL 2.1 compliant XML with:
- **VAT Compliance**: Proper VAT-exclusive calculations for Dutch tax requirements
- **Hostfact Integration**: Direct import compatibility
- **Complete Metadata**: Supplier/customer details, payment terms, IBAN support
- **Line Item Accuracy**: Descriptions, quantities, unit prices with VAT handling
- **Schema Validation**: Passes UBL 2.1 XML schema validation

## Configuration

### Configuration Files
- `pdf2ubl.json` - Main configuration
- `hostfact_config.json` - Hostfact-specific settings

### Environment Variables
All settings can be overridden with `PDF2UBL_` prefixed environment variables:
- `PDF2UBL_DEBUG=true` - Enable debug logging
- `PDF2UBL_USE_OCR=true` - Enable OCR for scanned PDFs
- `PDF2UBL_DEFAULT_VAT_RATE=21.0` - Default VAT rate
- `PDF2UBL_MIN_CONFIDENCE=0.3` - Minimum confidence threshold

## Testing and Validation

### Current Testing Approach
**No formal test suite** - the project uses validation scripts instead of pytest:

### Validation Scripts
```bash
# Comprehensive validation of all test invoices
python3 validate_tests2_comprehensive.py

# Convert all test PDFs to XML
python3 convert_tests2_to_xml.py

# Validate line items and VAT calculations
python3 validate_line_items_vat.py

# Test Hostfact integration fixes
python3 verify_hostfact_fix.py
```

### Test Results
- **95.7% Success Rate** (44/46 PDFs processed successfully)
- **100% Quality Score** (no validation errors)
- **Perfect UBL Compliance** for Hostfact import

### Adding Tests
If implementing formal tests, create:
- `tests/` directory
- `test_*.py` files using pytest
- Test fixtures for sample PDFs
- Mock templates for testing

## Development Workflow

### Setup
```bash
# Clone and setup
git clone <repository>
cd PDF2UBL

# Setup virtual environment
source ./activate.sh

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 verify_installation.py
```

### Key Development Files
- **Main Scripts**: `pdf2ubl.py`, `start_gui.py`, `activate.sh`
- **Validation**: `validate_tests2_comprehensive.py`, `verify_installation.py`
- **Template Tools**: `create_custom_template.py`
- **Documentation**: `README.md`, `QUICKSTART.md`, `TEMPLATE_GUIDE.md`, `GUI_README.md`

### No Build System
The project doesn't use:
- `setup.py` or `pyproject.toml` for packaging
- GitHub Actions or CI/CD
- Docker containers
- Makefile or build scripts

## Error Handling and Debugging

### Common Issues
1. **PDF extraction fails**: Enable OCR with `--use-ocr` or `PDF2UBL_USE_OCR=true`
2. **Template not found**: Use `--supplier-hint` or check `python3 -m src.pdf2ubl.cli template list`
3. **UBL validation errors**: Check extraction with `extract` command first
4. **Dutch date parsing**: System handles Nederlandse maandnamen automatically

### Debug Mode
```bash
# Enable verbose logging
python3 -m src.pdf2ubl.cli convert invoice.pdf --verbose

# Set debug environment
export PDF2UBL_DEBUG=true
export PDF2UBL_LOG_LEVEL=DEBUG
```

### Log Files
- `pdf2ubl.log` - Application logs
- Check console output for real-time debugging

## Hostfact Integration

### Optimization Features
- **Correct supplier extraction** (no "Unknown Supplier" errors)
- **VAT-exclusive line items** with proper tax calculations
- **Dutch date and currency formats**
- **IBAN payment information support**
- **Complete BTW (VAT) metadata**

### Import Process
1. Convert PDF with PDF2UBL
2. Import generated UBL XML into Hostfact
3. Verify supplier and line item data
4. Complete import process

## Key Files and Locations

### Core Application Files
- **`pdf2ubl.py`** - Main convenience entry point
- **`src/pdf2ubl/cli.py`** - CLI implementation
- **`src/pdf2ubl/templates/template_engine.py`** - Core extraction logic
- **`src/pdf2ubl/templates/template_manager.py`** - Template loading and detection
- **`src/pdf2ubl/exporters/ubl_exporter.py`** - UBL XML generation
- **`src/pdf2ubl/extractors/pdf_extractor.py`** - PDF parsing coordinator

### GUI Files
- **`src/pdf2ubl/gui/web/main.py`** - FastAPI backend
- **`src/pdf2ubl/gui/frontend/src/App.tsx`** - React frontend
- **`start_gui.py`** - GUI startup script

### Template Files
- **`templates/`** - All supplier-specific templates (13 files)
- **`templates/generic_nl.json`** - Fallback template

### Configuration and Setup
- **`requirements.txt`** - Python dependencies
- **`activate.sh`** - Virtual environment activation
- **`verify_installation.py`** - Installation verification

### Documentation
- **`README.md`** - Comprehensive Dutch documentation
- **`QUICKSTART.md`** - Quick start guide
- **`TEMPLATE_GUIDE.md`** - Template creation guide
- **`GUI_README.md`** - Web interface documentation

## Performance Characteristics

- **Multi-threading**: Batch processing with concurrent operations
- **Memory-efficient**: Streams large PDFs without loading entirely
- **Intelligent caching**: Template loading and ML model caching
- **Optimized regex**: Fast pattern matching for extraction
- **Progressive processing**: Handles large documents incrementally

## Current Limitations

1. **No formal test suite** - relies on validation scripts
2. **No packaging configuration** - no setup.py/pyproject.toml
3. **No CI/CD pipeline** - manual testing and validation
4. **No Docker support** - native Python installation required
5. **Dutch-focused** - primarily optimized for Dutch suppliers and formats

## Extension Points

### Adding New Suppliers
1. Create new template in `templates/supplier_nl.json`
2. Define supplier detection patterns
3. Add extraction rules for fields
4. Test with sample invoices
5. Optimize confidence thresholds

### Adding New Export Formats
1. Create new exporter in `src/pdf2ubl/exporters/`
2. Implement format-specific XML generation
3. Add CLI command for new format
4. Update GUI to support new format

### API Integration
1. Extend `src/pdf2ubl/api/` modules
2. Add new endpoints in GUI backend
3. Implement authentication if needed
4. Add rate limiting and validation

## Important Notes

- **Dutch Language**: Primary documentation is in Dutch, system optimized for Dutch suppliers
- **Hostfact Focus**: Special attention to Hostfact accounting software compatibility
- **Template-Driven**: Core functionality depends on supplier-specific templates
- **ML Enhancement**: Machine learning features complement but don't replace templates
- **UBL Compliance**: Strong focus on UBL 2.1 XML standard compliance
- **VAT Handling**: Sophisticated Dutch VAT calculation and compliance features