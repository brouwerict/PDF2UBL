#!/usr/bin/env python3
"""Sample usage examples for PDF2UBL library."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from pdf2ubl.extractors.pdf_extractor import PDFExtractor
from pdf2ubl.exporters.ubl_exporter import UBLExporter
from pdf2ubl.templates.template_manager import TemplateManager
from pdf2ubl.templates.template_engine import TemplateEngine
from pdf2ubl.utils.config import load_config


def example_1_basic_conversion():
    """Example 1: Basic PDF to UBL conversion."""
    print("=== Example 1: Basic PDF to UBL Conversion ===")
    
    # Initialize components
    pdf_extractor = PDFExtractor()
    ubl_exporter = UBLExporter()
    
    # Sample PDF path (you would use your actual PDF file)
    pdf_path = Path("sample_invoice.pdf")
    
    if not pdf_path.exists():
        print(f"Sample PDF not found: {pdf_path}")
        print("Please provide a real PDF file to test with.")
        return
    
    try:
        # Extract data from PDF
        print(f"Extracting data from: {pdf_path}")
        extracted_data = pdf_extractor.extract(pdf_path)
        
        # Show extracted data
        print(f"Invoice Number: {extracted_data.invoice_number}")
        print(f"Invoice Date: {extracted_data.invoice_date}")
        print(f"Supplier: {extracted_data.supplier_name}")
        print(f"Total Amount: €{extracted_data.total_amount}")
        
        # Generate UBL XML
        output_path = pdf_path.with_suffix('.xml')
        xml_content = ubl_exporter.export_to_ubl(extracted_data, output_path)
        
        print(f"UBL XML generated: {output_path}")
        print(f"XML length: {len(xml_content)} characters")
        
    except Exception as e:
        print(f"Error: {e}")


def example_2_template_based_extraction():
    """Example 2: Template-based extraction."""
    print("\n=== Example 2: Template-based Extraction ===")
    
    # Initialize components
    pdf_extractor = PDFExtractor()
    template_manager = TemplateManager()
    template_engine = TemplateEngine()
    ubl_exporter = UBLExporter()
    
    # Create default templates if they don't exist
    if not template_manager.get_templates():
        print("Creating default templates...")
        template_manager.create_default_templates()
    
    # Sample PDF path
    pdf_path = Path("sample_invoice.pdf")
    
    if not pdf_path.exists():
        print(f"Sample PDF not found: {pdf_path}")
        return
    
    try:
        # Extract raw data
        print(f"Extracting data from: {pdf_path}")
        extracted_data = pdf_extractor.extract(pdf_path)
        
        # Find best matching template
        print("Finding best template...")
        template = template_manager.find_best_template(extracted_data.raw_text)
        
        if template:
            print(f"Using template: {template.name}")
            
            # Apply template
            refined_data = template_engine.apply_template(
                template, 
                extracted_data.raw_text
            )
            
            # Show improved extraction
            print(f"Template confidence: {template_engine.get_extraction_quality(refined_data, template):.1%}")
            
            extracted_data = refined_data
        else:
            print("No suitable template found, using generic extraction")
        
        # Generate UBL XML
        output_path = pdf_path.with_suffix('_template.xml')
        ubl_exporter.export_to_ubl(extracted_data, output_path)
        
        print(f"Template-based UBL XML generated: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_3_custom_template():
    """Example 3: Create and use custom template."""
    print("\n=== Example 3: Custom Template Creation ===")
    
    from pdf2ubl.templates.template_models import Template, FieldPattern, ExtractionMethod, FieldType
    
    # Create custom template
    template = Template(
        template_id="example_company",
        name="Example Company B.V.",
        supplier_name="Example Company B.V.",
        description="Template for Example Company invoices"
    )
    
    # Add invoice number extraction rule
    template.add_field_rule(
        field_name="invoice_number",
        field_type=FieldType.TEXT,
        patterns=[
            FieldPattern(
                pattern=r'Invoice\s+(?:Number|Nr)[:\s]*(\w+)',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.TEXT,
                confidence_threshold=0.8,
                name="Invoice number pattern"
            )
        ],
        required=True
    )
    
    # Add total amount extraction rule
    template.add_field_rule(
        field_name="total_amount",
        field_type=FieldType.AMOUNT,
        patterns=[
            FieldPattern(
                pattern=r'Total[:\s]*€?\s*(\d+[.,]\d{2})',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.AMOUNT,
                confidence_threshold=0.8,
                name="Total amount pattern"
            )
        ],
        required=True
    )
    
    # Save template
    template_manager = TemplateManager()
    template_manager.save_template(template)
    
    print(f"Created custom template: {template.name}")
    print(f"Template ID: {template.template_id}")
    print(f"Extraction rules: {len(template.extraction_rules)}")


def example_4_batch_processing():
    """Example 4: Batch processing multiple PDFs."""
    print("\n=== Example 4: Batch Processing ===")
    
    # Create sample directory structure
    input_dir = Path("sample_pdfs")
    output_dir = Path("output_xml")
    
    if not input_dir.exists():
        print(f"Sample directory not found: {input_dir}")
        print("Please create a directory with PDF files to process.")
        return
    
    # Find PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Initialize components
    pdf_extractor = PDFExtractor()
    template_manager = TemplateManager()
    template_engine = TemplateEngine()
    ubl_exporter = UBLExporter()
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Process each file
    success_count = 0
    error_count = 0
    
    for pdf_file in pdf_files:
        try:
            print(f"Processing: {pdf_file.name}")
            
            # Extract data
            extracted_data = pdf_extractor.extract(pdf_file)
            
            # Find template
            template = template_manager.find_best_template(extracted_data.raw_text)
            
            if template:
                print(f"  Using template: {template.name}")
                extracted_data = template_engine.apply_template(
                    template, 
                    extracted_data.raw_text
                )
            
            # Generate output
            output_file = output_dir / pdf_file.with_suffix('.xml').name
            ubl_exporter.export_to_ubl(extracted_data, output_file)
            
            print(f"  Generated: {output_file.name}")
            success_count += 1
            
        except Exception as e:
            print(f"  Error: {e}")
            error_count += 1
    
    print(f"\nBatch processing completed:")
    print(f"  Successful: {success_count}")
    print(f"  Errors: {error_count}")


def example_5_configuration():
    """Example 5: Configuration management."""
    print("\n=== Example 5: Configuration Management ===")
    
    # Load configuration
    config = load_config()
    
    print(f"Current configuration:")
    print(f"  Debug mode: {config.debug}")
    print(f"  Templates directory: {config.templates_dir}")
    print(f"  Default currency: {config.default_currency}")
    print(f"  Default VAT rate: {config.default_vat_rate}%")
    print(f"  Use OCR: {config.use_ocr}")
    print(f"  OCR language: {config.ocr_language}")
    
    # Update configuration
    config.default_vat_rate = 19.0  # German VAT rate
    config.default_currency = "EUR"
    
    # Save configuration
    config_path = Path("pdf2ubl_example.json")
    config.save_to_file(config_path)
    
    print(f"\nConfiguration saved to: {config_path}")


def example_6_test_invoice():
    """Example 6: Generate test UBL invoice."""
    print("\n=== Example 6: Generate Test UBL Invoice ===")
    
    # Initialize exporter
    ubl_exporter = UBLExporter()
    
    # Generate test invoice
    test_invoice = ubl_exporter.create_test_invoice()
    
    print(f"Test invoice created:")
    print(f"  Invoice ID: {test_invoice.invoice_id}")
    print(f"  Issue Date: {test_invoice.issue_date}")
    print(f"  Supplier: {test_invoice.supplier.party_name}")
    print(f"  Customer: {test_invoice.customer.party_name}")
    print(f"  Line Items: {len(test_invoice.invoice_lines)}")
    
    # Generate XML
    output_path = Path("test_invoice_example.xml")
    xml_content = ubl_exporter.export_test_invoice(output_path)
    
    print(f"  XML generated: {output_path}")
    print(f"  XML length: {len(xml_content)} characters")
    
    # Validate XML
    is_valid = ubl_exporter.validate_ubl_xml(xml_content)
    print(f"  XML validation: {'PASSED' if is_valid else 'FAILED'}")


def main():
    """Run all examples."""
    print("PDF2UBL Library Usage Examples")
    print("=" * 50)
    
    try:
        example_1_basic_conversion()
        example_2_template_based_extraction()
        example_3_custom_template()
        example_4_batch_processing()
        example_5_configuration()
        example_6_test_invoice()
        
        print("\n" + "=" * 50)
        print("All examples completed!")
        print("\nTo run individual examples, modify this script or")
        print("call the specific example functions directly.")
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user.")
    except Exception as e:
        print(f"\nError running examples: {e}")


if __name__ == "__main__":
    main()