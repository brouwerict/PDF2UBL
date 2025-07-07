#!/usr/bin/env python3
"""Parse line items from invoice text."""

import sys
from pathlib import Path
import re

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def parse_line_items_from_text(text):
    """Parse line items from raw invoice text."""
    
    line_items = []
    
    # Look for lines that match the pattern: description € amount
    # Based on the user's examples:
    # SpamExperts inkomende filter: 1 domein, 25-04-2025 tot 25-05-2025 € 1,75
    # SpamExperts uitgaande filter: 5 domeinen, 25-04-2025 tot 25-05-2025 € 4,05
    # 13 .nl domeinnamen € 69,81
    # 8 .com domeinnamen € 92,04
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and non-relevant lines
        if not line or 'FACTUUR' in line or 'Factuurnummer' in line or 'Subtotaal' in line or 'BTW' in line or 'Totaal' in line:
            continue
            
        # Look for line item pattern: description € amount
        pattern = r'^(.+?)\s*€\s*(\d+[.,]\d{2})$'
        match = re.match(pattern, line)
        
        if match:
            description = match.group(1).strip()
            amount_str = match.group(2).replace(',', '.')
            amount = float(amount_str)
            
            # Filter out lines that look like line items
            if any(keyword in description.lower() for keyword in ['filter', 'domeinnamen', 'domein', '.nl', '.com', 'hosting', 'service']):
                line_items.append({
                    'description': description,
                    'quantity': 1,
                    'unit_price': amount,
                    'total_amount': amount
                })
                print(f"Found line item: {description} - €{amount:.2f}")
    
    return line_items

def test_line_items():
    """Test line item parsing."""
    
    from pdf2ubl.extractors.pdf_extractor import PDFExtractor
    
    pdf_file = Path("factuur_2503309_brouwerict.pdf")
    
    if not pdf_file.exists():
        print(f"❌ PDF file not found: {pdf_file}")
        return
    
    print(f"🔍 Parsing line items from: {pdf_file}")
    print("=" * 60)
    
    # Extract raw text
    extractor = PDFExtractor()
    extracted_data = extractor.extract(pdf_file)
    
    # Parse line items
    line_items = parse_line_items_from_text(extracted_data.raw_text)
    
    print(f"\n📋 FOUND {len(line_items)} LINE ITEMS:")
    print("-" * 40)
    
    total_line_items = 0
    for i, item in enumerate(line_items, 1):
        desc = item['description']
        amount = item['total_amount']
        print(f"{i:2d}. {desc:<50} €{amount:>7.2f}")
        total_line_items += amount
    
    print("-" * 40)
    print(f"Total line items: €{total_line_items:.2f}")
    
    # Compare with invoice totals
    print(f"\nFrom invoice text:")
    if '167,65' in extracted_data.raw_text:
        print(f"  Subtotal: €167.65")
    if '35,21' in extracted_data.raw_text:
        print(f"  VAT: €35.21")
    if '202,86' in extracted_data.raw_text:
        print(f"  Total: €202.86")
    
    print(f"\nDifference: €{167.65 - total_line_items:.2f}")

if __name__ == "__main__":
    test_line_items()