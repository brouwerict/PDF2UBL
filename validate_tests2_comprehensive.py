#!/usr/bin/env python3
"""
Comprehensive validation and optimization script for all invoices in tests2/ directory.
"""

import sys
import os
from pathlib import Path
import json
import logging
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf2ubl.extractors.pdf_extractor import PDFExtractor
from pdf2ubl.templates.template_manager import TemplateManager
from pdf2ubl.templates.template_engine import TemplateEngine
from pdf2ubl.exporters.ubl_exporter import UBLExporter

def analyze_tests2_invoices():
    """Comprehensive analysis of all invoices in tests2/ directory."""
    
    # Setup
    pdf_extractor = PDFExtractor()
    template_manager = TemplateManager()
    template_engine = TemplateEngine()
    ubl_exporter = UBLExporter()
    
    tests2_dir = Path("tests2")
    results = []
    supplier_stats = defaultdict(lambda: {"count": 0, "pdfs": [], "template_matched": 0})
    
    print("🔍 COMPREHENSIVE ANALYSIS: tests2/ invoices")
    print("=" * 70)
    
    # Get all PDF files
    pdf_files = [f for f in tests2_dir.glob("*.pdf") if not f.name.endswith(".Zone.Identifier")]
    
    for pdf_file in sorted(pdf_files):
        print(f"\n📄 Analyzing: {pdf_file.name}")
        
        try:
            # Extract PDF content
            extracted_data = pdf_extractor.extract(pdf_file)
            
            # Get sample text for supplier detection
            sample_text = extracted_data.raw_text[:2000] if extracted_data.raw_text else ""
            
            # Try to detect supplier from text patterns
            detected_suppliers = detect_suppliers_from_text(sample_text)
            print(f"   🏢 Detected suppliers: {detected_suppliers}")
            
            # Find best template
            best_template = template_manager.find_best_template(
                extracted_data.raw_text, 
                supplier_hint=""
            )
            
            template_name = best_template.name if best_template else "NO TEMPLATE"
            template_id = best_template.template_id if best_template else None
            
            print(f"   📋 Template: {template_name}")
            
            # Track supplier statistics
            primary_supplier = detected_suppliers[0] if detected_suppliers else "Unknown"
            supplier_stats[primary_supplier]["count"] += 1
            supplier_stats[primary_supplier]["pdfs"].append(pdf_file.name)
            if best_template:
                supplier_stats[primary_supplier]["template_matched"] += 1
            
            # Apply template if found
            processed_data = None
            if best_template:
                processed_data = template_engine.apply_template(
                    best_template,
                    extracted_data.raw_text,
                    extracted_data.tables,
                    extracted_data.positioned_text
                )
                
                # Show key extracted fields
                print(f"   💰 Invoice: {processed_data.invoice_number}")
                print(f"   📅 Date: {processed_data.invoice_date}")
                print(f"   💰 Total: €{processed_data.total_amount or 0:.2f}")
                print(f"   💰 Net: €{processed_data.net_amount or 0:.2f}")
                print(f"   💰 VAT: €{processed_data.vat_amount or 0:.2f}")
                print(f"   📝 Line Items: {len(processed_data.line_items)}")
                
                # Calculate line item totals
                line_items_total = sum(getattr(item, 'total_amount', 0) if hasattr(item, 'total_amount') else item.get('total_amount', 0) for item in processed_data.line_items)
                print(f"   📊 Line Items Total: €{line_items_total:.2f}")
                
                # Check for VAT calculation issues
                issues = []
                if processed_data.total_amount and line_items_total > 0:
                    diff = abs(float(processed_data.total_amount) - line_items_total)
                    if diff > 0.02:  # Allow 2 cent rounding
                        issues.append(f"Line items total ({line_items_total:.2f}) ≠ header total ({processed_data.total_amount:.2f})")
                
                if processed_data.net_amount and processed_data.vat_amount and processed_data.total_amount:
                    calculated_total = float(processed_data.net_amount) + float(processed_data.vat_amount)
                    if abs(calculated_total - float(processed_data.total_amount)) > 0.02:
                        issues.append(f"Net + VAT ({calculated_total:.2f}) ≠ total ({processed_data.total_amount:.2f})")
                
                if issues:
                    print(f"   ⚠️  Issues: {'; '.join(issues)}")
                else:
                    print(f"   ✅ Perfect calculations!")
            
            # Test UBL conversion
            ubl_success = False
            if processed_data:
                try:
                    ubl_xml = ubl_exporter.export_to_ubl(processed_data)
                    ubl_success = True
                    print(f"   ✅ UBL Conversion: Success")
                except Exception as e:
                    print(f"   ❌ UBL Conversion Error: {e}")
            
            # Store detailed results
            result = {
                "pdf_file": pdf_file.name,
                "detected_suppliers": detected_suppliers,
                "template_matched": template_name,
                "template_id": template_id,
                "has_template": best_template is not None,
                "ubl_conversion_success": ubl_success,
                "extracted_data": {
                    "invoice_number": str(processed_data.invoice_number) if processed_data and processed_data.invoice_number else None,
                    "invoice_date": str(processed_data.invoice_date) if processed_data and processed_data.invoice_date else None,
                    "supplier_name": str(processed_data.supplier_name) if processed_data and processed_data.supplier_name else None,
                    "total_amount": float(processed_data.total_amount) if processed_data and processed_data.total_amount else 0.0,
                    "net_amount": float(processed_data.net_amount) if processed_data and processed_data.net_amount else 0.0,
                    "vat_amount": float(processed_data.vat_amount) if processed_data and processed_data.vat_amount else 0.0,
                    "line_items_count": len(processed_data.line_items) if processed_data else 0,
                    "line_items_total": line_items_total if processed_data else 0.0
                },
                "issues": issues if processed_data else ["No template matched"],
                "sample_text": sample_text[:500]  # First 500 chars for analysis
            }
            
            results.append(result)
            
        except Exception as e:
            print(f"   💥 Processing Error: {e}")
            supplier_stats["Error"]["count"] += 1
            supplier_stats["Error"]["pdfs"].append(pdf_file.name)
            
            results.append({
                "pdf_file": pdf_file.name,
                "detected_suppliers": [],
                "template_matched": "ERROR",
                "has_template": False,
                "ubl_conversion_success": False,
                "issues": [f"Processing error: {str(e)}"],
                "sample_text": ""
            })
    
    # Generate comprehensive report
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE ANALYSIS REPORT")
    print("=" * 70)
    
    total_pdfs = len(results)
    successful_templates = len([r for r in results if r["has_template"]])
    successful_ubl = len([r for r in results if r["ubl_conversion_success"]])
    
    print(f"Total PDFs analyzed: {total_pdfs}")
    print(f"Successfully matched templates: {successful_templates} ({successful_templates/total_pdfs*100:.1f}%)")
    print(f"Successful UBL conversions: {successful_ubl} ({successful_ubl/total_pdfs*100:.1f}%)")
    
    # Supplier breakdown
    print(f"\n🏢 SUPPLIER BREAKDOWN:")
    for supplier, stats in sorted(supplier_stats.items(), key=lambda x: x[1]["count"], reverse=True):
        print(f"\n📋 {supplier}:")
        print(f"   Count: {stats['count']} PDFs")
        print(f"   Template Match Rate: {stats['template_matched']}/{stats['count']} ({stats['template_matched']/stats['count']*100:.0f}%)")
        print(f"   Files: {', '.join(stats['pdfs'][:5])}{'...' if len(stats['pdfs']) > 5 else ''}")
    
    # Templates that need creation
    print(f"\n🎯 MISSING TEMPLATES NEEDED:")
    for supplier, stats in supplier_stats.items():
        if supplier not in ["Unknown", "Error"] and stats["template_matched"] < stats["count"]:
            missing_rate = (stats["count"] - stats["template_matched"]) / stats["count"]
            if missing_rate > 0.3:  # More than 30% not matched
                print(f"\n🔨 {supplier}: Needs template creation")
                print(f"   Missing matches: {stats['count'] - stats['template_matched']}/{stats['count']} ({missing_rate*100:.0f}%)")
                print(f"   Sample files: {', '.join(stats['pdfs'][:3])}")
    
    # Detailed issues analysis
    print(f"\n🔧 DETAILED ISSUES ANALYSIS:")
    issue_types = defaultdict(list)
    
    for result in results:
        for issue in result.get("issues", []):
            issue_types[issue].append(result["pdf_file"])
    
    for issue, files in sorted(issue_types.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n❗ {issue}:")
        print(f"   Affected files ({len(files)}): {', '.join(files[:5])}{'...' if len(files) > 5 else ''}")
    
    # Save detailed results
    with open("tests2_comprehensive_analysis.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: tests2_comprehensive_analysis.json")
    
    return results, supplier_stats

def detect_suppliers_from_text(text: str) -> list:
    """Detect potential suppliers from invoice text."""
    
    suppliers = []
    text_lower = text.lower()
    
    # Known supplier patterns
    supplier_patterns = {
        "Proserve": ["proserve", "proserve b.v."],
        "VDX Nederland": ["vdx", "vdx nederland"],
        "123accu": ["123accu", "123 accu"],
        "DectDirect": ["dectdirect", "dect direct"],
        "WeServit": ["weservit", "weservcloud", "weserv cloud"],
        "NextName": ["nextname", "next name"],
        "Opslagruimte": ["opslagruimte", "haaksbergen"],
        "CheapConnect": ["cheapconnect", "cheap connect"],
        "Fonu": ["fonu"],
    }
    
    for supplier, patterns in supplier_patterns.items():
        for pattern in patterns:
            if pattern in text_lower:
                if supplier not in suppliers:
                    suppliers.append(supplier)
                break
    
    # Try to extract company names from common patterns
    import re
    
    # Look for company patterns
    company_patterns = [
        r'\b([A-Z][a-zA-Z\s]+?)\s+B\.?V\.?\b',
        r'\b([A-Z][a-zA-Z]+)\s+Nederland\b',
        r'^\s*([A-Z][a-zA-Z\s]+?)\s*$',  # Lines with just company names
    ]
    
    for pattern in company_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for match in matches:
            clean_match = match.strip()
            if len(clean_match) > 3 and clean_match not in suppliers:
                # Filter out common non-company words
                if not any(word in clean_match.lower() for word in ['factuur', 'invoice', 'datum', 'nummer', 'bedrag', 'totaal']):
                    suppliers.append(clean_match)
                    break
    
    return suppliers[:3]  # Return top 3 detected suppliers

if __name__ == "__main__":
    # Set up logging to reduce noise
    logging.getLogger().setLevel(logging.WARNING)
    
    results, supplier_stats = analyze_tests2_invoices()