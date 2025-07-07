# PDF2UBL Quick Start Guide

This guide will get you up and running with PDF2UBL in just a few minutes.

## 🚀 Installation

### 1. Activate Virtual Environment
```bash
source ./activate.sh
```

### 2. Verify Installation
```bash
python verify_installation.py
```

You should see all green checkmarks ✓

## 📋 Basic Usage

### 1. Initialize Templates
```bash
./pdf2ubl.py template init
```

### 2. Generate Test Invoice
```bash
./pdf2ubl.py test
```
This creates `test_invoice.xml` - a valid UBL XML file.

### 3. List Available Templates
```bash
./pdf2ubl.py template list
```

### 4. Convert Your First PDF
```bash
./pdf2ubl.py convert your_invoice.pdf
```

This will:
- Extract data from the PDF
- Find the best matching template
- Generate UBL XML (`your_invoice.xml`)

### 5. Preview Extraction (No XML Generated)
```bash
./pdf2ubl.py convert your_invoice.pdf --preview
```

## 📂 Batch Processing

Convert multiple PDFs at once:

```bash
./pdf2ubl.py batch /path/to/pdf/folder --output-dir /path/to/xml/output
```

## ⚙️ Advanced Usage

### Using Specific Templates
```bash
./pdf2ubl.py convert invoice.pdf --template kpn_nl
```

### Supplier Hint for Better Template Selection
```bash
./pdf2ubl.py convert invoice.pdf --supplier-hint "KPN"
```

### Extract Data Only (No UBL Generation)
```bash
./pdf2ubl.py extract invoice.pdf
```

## 🔧 Template Management

### Create New Template
```bash
./pdf2ubl.py template create my_supplier "My Supplier B.V." --supplier "My Supplier B.V."
```

### View Template Statistics
```bash
./pdf2ubl.py template stats
```

### Delete Template
```bash
./pdf2ubl.py template delete my_supplier --confirm
```

## 📊 Configuration

Create a configuration file `pdf2ubl.json`:

```json
{
  "debug": false,
  "use_ocr": false,
  "default_currency": "EUR",
  "default_vat_rate": 21.0,
  "min_confidence": 0.3
}
```

Or use environment variables:
```bash
export PDF2UBL_DEBUG=true
export PDF2UBL_USE_OCR=true
export PDF2UBL_DEFAULT_VAT_RATE=19.0
```

## 🎯 Common Use Cases

### 1. Dutch Company Processing Supplier Invoices
```bash
# Initialize with Dutch templates
./pdf2ubl.py template init

# Process KPN invoice
./pdf2ubl.py convert kpn_invoice.pdf

# Process Ziggo invoice  
./pdf2ubl.py convert ziggo_invoice.pdf

# Process unknown supplier (auto-detect)
./pdf2ubl.py convert unknown_invoice.pdf
```

### 2. Batch Processing Month-End Invoices
```bash
# Process all PDFs in folder
./pdf2ubl.py batch invoices/2024-01/ --output-dir ubl/2024-01/

# Continue on errors
./pdf2ubl.py batch invoices/2024-01/ --continue-on-error
```

### 3. Testing and Validation
```bash
# Generate test invoice for validation
./pdf2ubl.py test --output validation_test.xml

# Preview extraction without generating UBL
./pdf2ubl.py convert problem_invoice.pdf --preview

# Use specific template for testing
./pdf2ubl.py convert test_invoice.pdf --template generic_nl --preview
```

## 🔍 Troubleshooting

### PDF Not Processing Correctly
1. Try preview mode: `./pdf2ubl.py convert file.pdf --preview`
2. Enable verbose logging: `./pdf2ubl.py --verbose convert file.pdf`
3. Try with OCR: Set `PDF2UBL_USE_OCR=true`

### Template Not Matching
1. Use supplier hint: `--supplier-hint "Company Name"`
2. List templates: `./pdf2ubl.py template list`
3. Create custom template for new supplier

### UBL Validation Errors
1. Check extraction quality in preview mode
2. Verify required fields are extracted
3. Check log files: `pdf2ubl.log`

## 📖 More Information

- Full documentation: [README.md](README.md)
- Configuration options: [src/pdf2ubl/utils/config.py](src/pdf2ubl/utils/config.py)
- Template examples: [templates/](templates/)
- Code examples: [examples/sample_usage.py](examples/sample_usage.py)

## 🆘 Getting Help

```bash
./pdf2ubl.py --help
./pdf2ubl.py convert --help
./pdf2ubl.py template --help
```

Happy invoicing! 🧾✨