#!/usr/bin/env python3
"""
Comprehensive validation script for line items and VAT calculations in PDF2UBL.
"""

import sys
import os
from pathlib import Path
import json
import logging
from decimal import Decimal, ROUND_HALF_UP

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf2ubl.extractors.pdf_extractor import PDFExtractor
from pdf2ubl.templates.template_manager import TemplateManager
from pdf2ubl.templates.template_engine import TemplateEngine
from pdf2ubl.exporters.ubl_exporter import UBLExporter

def validate_line_items_and_vat():
    """Validate line items extraction and VAT calculations for all test PDFs."""
    
    # Setup
    pdf_extractor = PDFExtractor()
    template_manager = TemplateManager()
    template_engine = TemplateEngine()
    ubl_exporter = UBLExporter()
    
    tests_dir = Path("tests")
    results = []
    
    print("🔍 Validating Line Items & VAT Calculations")
    print("=" * 60)
    
    # Get all PDF files
    pdf_files = list(tests_dir.glob("*.pdf")) + list(tests_dir.glob("*.PDF"))
    
    for pdf_file in sorted(pdf_files):
        print(f"\n📄 Analyzing: {pdf_file.name}")
        
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
                continue
                
            print(f"   📋 Template: {best_template.name}")
            
            # Apply template
            processed_data = template_engine.apply_template(
                best_template,
                extracted_data.raw_text,
                extracted_data.tables,
                extracted_data.positioned_text
            )
            
            # Generate UBL XML to test full pipeline
            try:
                ubl_xml = ubl_exporter.export_to_ubl(processed_data)
                conversion_success = True
            except Exception as e:
                ubl_xml = None
                conversion_success = False
                print(f"   💥 UBL Export Error: {e}")
            
            # Analyze line items
            line_items = processed_data.line_items
            line_items_count = len(line_items)
            
            print(f"   📝 Line Items: {line_items_count}")
            
            # Show first few line items for inspection
            for i, item in enumerate(line_items[:3]):
                if hasattr(item, 'description'):
                    # Line item is an object
                    print(f"     {i+1}. {item.description[:50]}")
                    print(f"        Qty: {item.quantity}, Unit: €{item.unit_price:.2f}, Total: €{item.total_amount:.2f}")
                else:
                    # Line item is a dict
                    print(f"     {i+1}. {item.get('description', 'Unknown')[:50]}")
                    print(f"        Qty: {item.get('quantity', 0)}, Unit: €{item.get('unit_price', 0):.2f}, Total: €{item.get('total_amount', 0):.2f}")
            
            if line_items_count > 3:
                print(f"     ... and {line_items_count - 3} more items")
            
            # Analyze financial data
            total_amount = processed_data.total_amount or 0
            net_amount = processed_data.net_amount or 0
            vat_amount = processed_data.vat_amount or 0
            
            print(f"   💰 Financial Summary:")
            print(f"     Total Amount: €{total_amount:.2f}")
            print(f"     Net Amount: €{net_amount:.2f}")
            print(f"     VAT Amount: €{vat_amount:.2f}")
            
            # Calculate line items totals
            line_items_total = 0
            line_items_net = 0
            line_items_vat = 0
            
            for item in line_items:
                if hasattr(item, 'total_amount'):
                    # Line item is an object
                    line_items_total += item.total_amount or 0
                    line_items_net += item.net_amount or 0
                    line_items_vat += item.vat_amount or 0
                else:
                    # Line item is a dict
                    line_items_total += item.get('total_amount', 0) or 0
                    line_items_net += item.get('net_amount', 0) or 0
                    line_items_vat += item.get('vat_amount', 0) or 0
            
            if line_items_count > 0:
                print(f"   📊 Line Items Totals:")
                print(f"     Items Total: €{line_items_total:.2f}")
                if line_items_net > 0:
                    print(f"     Items Net: €{line_items_net:.2f}")
                if line_items_vat > 0:
                    print(f"     Items VAT: €{line_items_vat:.2f}")
            
            # VAT validation
            vat_issues = []
            
            # Check if amounts make sense
            if total_amount > 0 and net_amount > 0 and vat_amount > 0:
                calculated_total = net_amount + vat_amount
                total_diff = abs(calculated_total - total_amount)
                
                if total_diff > 0.02:  # Allow 2 cent rounding difference
                    vat_issues.append(f"Total mismatch: {net_amount:.2f} + {vat_amount:.2f} = {calculated_total:.2f} ≠ {total_amount:.2f}")
                
                # Check VAT percentage (assuming 21% Dutch standard)
                if net_amount > 0:
                    vat_percentage = (vat_amount / net_amount) * 100
                    if abs(vat_percentage - 21.0) > 1.0:  # Allow 1% difference
                        vat_issues.append(f"VAT rate: {vat_percentage:.1f}% (expected ~21%)")
            
            # Check line items vs header totals
            if line_items_count > 0 and line_items_total > 0:
                if total_amount > 0:
                    items_vs_total_diff = abs(line_items_total - total_amount)
                    if items_vs_total_diff > 0.02:
                        vat_issues.append(f"Line items total {line_items_total:.2f} ≠ header total {total_amount:.2f}")
            
            # Overall assessment
            issues = []
            
            if line_items_count == 0:
                issues.append("No line items extracted")
            
            if total_amount == 0:
                issues.append("Missing total amount")
                
            if not conversion_success:
                issues.append("UBL conversion failed")
            
            if vat_issues:
                issues.extend(vat_issues)
            
            # Success indicators
            if not issues:
                print(f"   ✅ Perfect extraction & calculations")
            else:
                print(f"   ⚠️  Issues: {'; '.join(issues)}")
            
            # Store results
            result = {
                "pdf_file": pdf_file.name,
                "template_used": best_template.name,
                "template_id": best_template.template_id,
                "line_items_count": line_items_count,
                "line_items_total": float(line_items_total),
                "header_total": float(total_amount),
                "header_net": float(net_amount),
                "header_vat": float(vat_amount),
                "ubl_conversion_success": conversion_success,
                "issues": issues,
                "line_items_sample": [
                    {
                        "description": item.description if hasattr(item, 'description') else item.get('description', 'Unknown'),
                        "quantity": item.quantity if hasattr(item, 'quantity') else item.get('quantity', 0),
                        "unit_price": float(item.unit_price if hasattr(item, 'unit_price') else item.get('unit_price', 0)),
                        "total_amount": float(item.total_amount if hasattr(item, 'total_amount') else item.get('total_amount', 0)),
                        "net_amount": float(item.net_amount) if (hasattr(item, 'net_amount') and item.net_amount) else (float(item.get('net_amount', 0)) if item.get('net_amount') else None),
                        "vat_amount": float(item.vat_amount) if (hasattr(item, 'vat_amount') and item.vat_amount) else (float(item.get('vat_amount', 0)) if item.get('vat_amount') else None),
                        "vat_rate": float(item.vat_rate) if (hasattr(item, 'vat_rate') and item.vat_rate) else (float(item.get('vat_rate', 0)) if item.get('vat_rate') else None)
                    }
                    for item in line_items[:3]  # First 3 items
                ]
            }
            
            results.append(result)
            
        except Exception as e:
            print(f"   💥 Processing Error: {e}")
            results.append({
                "pdf_file": pdf_file.name,
                "template_used": "ERROR",
                "template_id": None,
                "line_items_count": 0,
                "issues": [f"Processing error: {str(e)}"]
            })
    
    # Generate comprehensive report
    print("\n" + "=" * 60)
    print("📊 LINE ITEMS & VAT VALIDATION REPORT")
    print("=" * 60)
    
    total_pdfs = len(results)
    pdfs_with_line_items = len([r for r in results if r.get("line_items_count", 0) > 0])
    pdfs_with_issues = len([r for r in results if r.get("issues", [])])
    successful_conversions = len([r for r in results if r.get("ubl_conversion_success", False)])
    
    print(f"Total PDFs analyzed: {total_pdfs}")
    print(f"PDFs with line items: {pdfs_with_line_items} ({pdfs_with_line_items/total_pdfs*100:.1f}%)")
    print(f"Successful UBL conversions: {successful_conversions} ({successful_conversions/total_pdfs*100:.1f}%)")
    print(f"PDFs with issues: {pdfs_with_issues} ({pdfs_with_issues/total_pdfs*100:.1f}%)")
    
    # Group by template
    template_stats = {}
    for result in results:
        template = result.get("template_used", "Unknown")
        if template not in template_stats:
            template_stats[template] = {
                "count": 0,
                "with_line_items": 0,
                "avg_line_items": 0,
                "issues": 0
            }
        
        stats = template_stats[template]
        stats["count"] += 1
        
        line_items_count = result.get("line_items_count", 0)
        if line_items_count > 0:
            stats["with_line_items"] += 1
            stats["avg_line_items"] += line_items_count
        
        if result.get("issues", []):
            stats["issues"] += 1
    
    # Calculate averages
    for template, stats in template_stats.items():
        if stats["with_line_items"] > 0:
            stats["avg_line_items"] = stats["avg_line_items"] / stats["with_line_items"]
    
    print(f"\n📋 Template Performance:")
    for template, stats in sorted(template_stats.items()):
        print(f"  {template}:")
        print(f"    PDFs: {stats['count']}")
        print(f"    With line items: {stats['with_line_items']}/{stats['count']} ({stats['with_line_items']/stats['count']*100:.0f}%)")
        if stats["avg_line_items"] > 0:
            print(f"    Avg line items: {stats['avg_line_items']:.1f}")
        print(f"    Issues: {stats['issues']}/{stats['count']} ({stats['issues']/stats['count']*100:.0f}%)")
    
    # Identify templates needing line item optimization
    print(f"\n🔧 TEMPLATES NEEDING LINE ITEM OPTIMIZATION:")
    
    for template, stats in sorted(template_stats.items()):
        if template == "ERROR":
            continue
            
        line_item_rate = stats["with_line_items"] / stats["count"] if stats["count"] > 0 else 0
        issue_rate = stats["issues"] / stats["count"] if stats["count"] > 0 else 0
        
        if line_item_rate < 0.8 or issue_rate > 0.5:  # Less than 80% with line items or >50% issues
            print(f"\n🎯 {template}: Needs optimization")
            print(f"   Line item extraction: {line_item_rate*100:.0f}%")
            print(f"   Issue rate: {issue_rate*100:.0f}%")
            
            # Show specific issues
            template_results = [r for r in results if r.get("template_used") == template]
            for result in template_results:
                if result.get("issues"):
                    print(f"   - {result['pdf_file']}: {'; '.join(result['issues'])}")
    
    # Save detailed results
    with open("line_items_vat_validation.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: line_items_vat_validation.json")
    
    return results

if __name__ == "__main__":
    # Set up logging to reduce noise
    logging.getLogger().setLevel(logging.WARNING)
    
    results = validate_line_items_and_vat()