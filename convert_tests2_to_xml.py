#!/usr/bin/env python3
"""
Convert all PDFs in tests2/ to UBL XML and validate the results.
"""

import sys
import os
from pathlib import Path
import json
import logging
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf2ubl.extractors.pdf_extractor import PDFExtractor
from pdf2ubl.templates.template_manager import TemplateManager
from pdf2ubl.templates.template_engine import TemplateEngine
from pdf2ubl.exporters.ubl_exporter import UBLExporter

def convert_all_tests2_to_xml():
    """Convert all PDFs in tests2/ to UBL XML files."""
    
    # Setup
    pdf_extractor = PDFExtractor()
    template_manager = TemplateManager()
    template_engine = TemplateEngine()
    ubl_exporter = UBLExporter()
    
    tests2_dir = Path("tests2")
    xml_output_dir = Path("tests2_xml_output")
    
    # Create output directory
    xml_output_dir.mkdir(exist_ok=True)
    
    results = []
    successful_conversions = 0
    failed_conversions = 0
    
    print("🔄 CONVERTING ALL tests2/ PDFs TO UBL XML")
    print("=" * 70)
    
    # Get all PDF files
    pdf_files = [f for f in tests2_dir.glob("*.pdf") if not f.name.endswith(".Zone.Identifier")]
    
    for pdf_file in sorted(pdf_files):
        print(f"\n📄 Converting: {pdf_file.name}")
        
        try:
            # Extract PDF content
            extracted_data = pdf_extractor.extract(pdf_file)
            
            # Find best template
            best_template = template_manager.find_best_template(
                extracted_data.raw_text, 
                supplier_hint=""
            )
            
            if not best_template:
                print(f"   ❌ No template found")
                failed_conversions += 1
                results.append({
                    "pdf_file": pdf_file.name,
                    "status": "failed",
                    "reason": "No template found",
                    "xml_file": None
                })
                continue
                
            print(f"   📋 Template: {best_template.name}")
            
            # Apply template
            processed_data = template_engine.apply_template(
                best_template,
                extracted_data.raw_text,
                extracted_data.tables,
                extracted_data.positioned_text
            )
            
            # Create XML filename
            xml_filename = pdf_file.stem + ".xml"
            xml_path = xml_output_dir / xml_filename
            
            # Generate UBL XML
            ubl_xml = ubl_exporter.export_to_ubl(
                processed_data,
                output_path=xml_path
            )
            
            # Validate the generated XML
            xml_valid = validate_ubl_xml(xml_path)
            
            print(f"   ✅ XML created: {xml_filename}")
            print(f"   📊 Invoice: {processed_data.invoice_number}")
            print(f"   💰 Total: €{processed_data.total_amount or 0:.2f}")
            print(f"   📝 Line Items: {len(processed_data.line_items)}")
            print(f"   ✓ XML Valid: {'Yes' if xml_valid else 'No'}")
            
            successful_conversions += 1
            
            results.append({
                "pdf_file": pdf_file.name,
                "status": "success",
                "template_used": best_template.name,
                "template_id": best_template.template_id,
                "xml_file": xml_filename,
                "xml_valid": xml_valid,
                "extracted_data": {
                    "invoice_number": str(processed_data.invoice_number) if processed_data.invoice_number else None,
                    "invoice_date": str(processed_data.invoice_date) if processed_data.invoice_date else None,
                    "supplier_name": str(processed_data.supplier_name) if processed_data.supplier_name else None,
                    "total_amount": float(processed_data.total_amount) if processed_data.total_amount else 0.0,
                    "net_amount": float(processed_data.net_amount) if processed_data.net_amount else 0.0,
                    "vat_amount": float(processed_data.vat_amount) if processed_data.vat_amount else 0.0,
                    "line_items_count": len(processed_data.line_items),
                    "currency": processed_data.currency
                },
                "xml_size_bytes": xml_path.stat().st_size if xml_path.exists() else 0
            })
            
        except Exception as e:
            print(f"   💥 Conversion Error: {e}")
            failed_conversions += 1
            
            results.append({
                "pdf_file": pdf_file.name,
                "status": "failed",
                "reason": str(e),
                "xml_file": None
            })
    
    # Generate comprehensive report
    print("\n" + "=" * 70)
    print("📊 CONVERSION RESULTS SUMMARY")
    print("=" * 70)
    
    total_pdfs = len(pdf_files)
    success_rate = (successful_conversions / total_pdfs * 100) if total_pdfs > 0 else 0
    
    print(f"Total PDFs processed: {total_pdfs}")
    print(f"Successful conversions: {successful_conversions} ({success_rate:.1f}%)")
    print(f"Failed conversions: {failed_conversions}")
    print(f"XML files created in: {xml_output_dir}")
    
    # Template usage statistics
    template_stats = {}
    for result in results:
        if result["status"] == "success":
            template = result["template_used"]
            if template not in template_stats:
                template_stats[template] = {"count": 0, "files": []}
            template_stats[template]["count"] += 1
            template_stats[template]["files"].append(result["pdf_file"])
    
    print(f"\n📋 Template Usage:")
    for template, stats in sorted(template_stats.items(), key=lambda x: x[1]["count"], reverse=True):
        print(f"  {template}: {stats['count']} files")
        print(f"    Files: {', '.join(stats['files'][:3])}{'...' if len(stats['files']) > 3 else ''}")
    
    # Quality analysis
    print(f"\n🎯 Quality Analysis:")
    
    valid_xml_count = len([r for r in results if r.get("xml_valid", False)])
    if successful_conversions > 0:
        xml_validity_rate = (valid_xml_count / successful_conversions * 100)
        print(f"Valid XML files: {valid_xml_count}/{successful_conversions} ({xml_validity_rate:.1f}%)")
    
    # File size analysis
    xml_files = [r for r in results if r.get("xml_size_bytes", 0) > 0]
    if xml_files:
        avg_size = sum(r["xml_size_bytes"] for r in xml_files) / len(xml_files)
        max_size = max(r["xml_size_bytes"] for r in xml_files)
        min_size = min(r["xml_size_bytes"] for r in xml_files)
        
        print(f"XML file sizes: avg {avg_size:.0f} bytes, min {min_size} bytes, max {max_size} bytes")
    
    # Failed conversions analysis
    if failed_conversions > 0:
        print(f"\n❌ Failed Conversions:")
        failed_results = [r for r in results if r["status"] == "failed"]
        failure_reasons = {}
        
        for result in failed_results:
            reason = result.get("reason", "Unknown error")
            if reason not in failure_reasons:
                failure_reasons[reason] = []
            failure_reasons[reason].append(result["pdf_file"])
        
        for reason, files in failure_reasons.items():
            print(f"  {reason}: {len(files)} files")
            print(f"    Files: {', '.join(files[:3])}{'...' if len(files) > 3 else ''}")
    
    # Save detailed results
    with open("tests2_xml_conversion_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: tests2_xml_conversion_results.json")
    
    return results

def validate_ubl_xml(xml_path: Path) -> bool:
    """Basic validation of UBL XML file."""
    try:
        if not xml_path.exists():
            return False
            
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic checks
        if len(content) < 100:  # Too small to be valid UBL
            return False
            
        # Check for required UBL elements
        required_elements = [
            '<?xml version=',
            'Invoice xmlns=',
            'ID>',
            'IssueDate>',
            'DocumentCurrencyCode>',
            'AccountingSupplierParty>',
            'AccountingCustomerParty>',
            'LegalMonetaryTotal>'
        ]
        
        for element in required_elements:
            if element not in content:
                return False
        
        return True
        
    except Exception:
        return False

if __name__ == "__main__":
    # Set up logging to reduce noise
    logging.getLogger().setLevel(logging.WARNING)
    
    results = convert_all_tests2_to_xml()