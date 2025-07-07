#!/usr/bin/env python3
"""Voorbeeld: Hoe je een custom template kunt maken voor een specifieke leverancier."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from pdf2ubl.templates.template_manager import TemplateManager
from pdf2ubl.templates.template_models import FieldPattern, ExtractionMethod, FieldType

def create_mediamarkt_template():
    """Maak een custom template voor MediaMarkt facturen."""
    
    template_manager = TemplateManager()
    
    # Maak nieuwe template
    mediamarkt_template = template_manager.create_template(
        template_id="mediamarkt_nl",
        name="MediaMarkt Nederland", 
        supplier_name="MediaMarkt",
        description="Template voor MediaMarkt facturen"
    )
    
    # Voeg specifieke MediaMarkt patronen toe
    
    # 1. Invoice number patterns (MediaMarkt heeft vaak MM- prefix)
    mediamarkt_template.add_field_rule(
        field_name="invoice_number",
        field_type=FieldType.TEXT,
        patterns=[
            FieldPattern(
                pattern=r'Factuurnummer[:\s]+(MM-?\d+)',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.TEXT,
                confidence_threshold=0.9,
                name="MediaMarkt invoice number",
                priority=15
            ),
            FieldPattern(
                pattern=r'(MM-?\d{6,})',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.TEXT, 
                confidence_threshold=0.8,
                name="MediaMarkt MM prefix pattern",
                priority=12
            )
        ],
        required=True
    )
    
    # 2. Supplier detection patterns
    mediamarkt_template.supplier_patterns = [
        FieldPattern(
            pattern=r'MediaMarkt',
            method=ExtractionMethod.REGEX,
            field_type=FieldType.TEXT,
            confidence_threshold=0.9,
            name="MediaMarkt company name"
        )
    ]
    
    # 3. MediaMarkt-specifieke bedrag patronen
    mediamarkt_template.add_field_rule(
        field_name="total_amount",
        field_type=FieldType.AMOUNT,
        patterns=[
            FieldPattern(
                pattern=r'Totaalbedrag[:\s]*€\s*(\d+[.,]\d{2})',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.AMOUNT,
                confidence_threshold=0.9,
                name="MediaMarkt totaalbedrag",
                priority=15
            )
        ],
        required=True
    )
    
    # 4. BTW patronen
    mediamarkt_template.add_field_rule(
        field_name="vat_amount",
        field_type=FieldType.AMOUNT,
        patterns=[
            FieldPattern(
                pattern=r'BTW\s+21%[:\s]*€\s*(\d+[.,]\d{2})',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.AMOUNT,
                confidence_threshold=0.9,
                name="MediaMarkt BTW 21%",
                priority=12
            )
        ]
    )
    
    # 5. Datum patronen
    mediamarkt_template.add_field_rule(
        field_name="invoice_date",
        field_type=FieldType.DATE,
        patterns=[
            FieldPattern(
                pattern=r'Factuurdatum[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.DATE,
                confidence_threshold=0.9,
                name="MediaMarkt factuurdatum",
                priority=12
            )
        ],
        required=True
    )
    
    # Sla template op
    template_manager.save_template(mediamarkt_template)
    
    print("✅ MediaMarkt template aangemaakt!")
    print("📁 Bestand: templates/mediamarkt_nl.json")
    print("🔧 Gebruik: python3 -m src.pdf2ubl.cli convert factuur.pdf -t mediamarkt_nl")
    
    return mediamarkt_template

def create_albert_heijn_template():
    """Maak een template voor Albert Heijn facturen."""
    
    template_manager = TemplateManager()
    
    ah_template = template_manager.create_template(
        template_id="ah_nl",
        name="Albert Heijn Nederland",
        supplier_name="Albert Heijn B.V.",
        description="Template voor Albert Heijn facturen"
    )
    
    # Albert Heijn specifieke patronen
    ah_template.add_field_rule(
        field_name="invoice_number",
        field_type=FieldType.TEXT,
        patterns=[
            FieldPattern(
                pattern=r'Bonnummer[:\s]+(\d{10,})',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.TEXT,
                confidence_threshold=0.9,
                name="AH bonnummer",
                priority=15
            )
        ],
        required=True
    )
    
    # Supplier detection
    ah_template.supplier_patterns = [
        FieldPattern(
            pattern=r'Albert\s+Heijn',
            method=ExtractionMethod.REGEX,
            field_type=FieldType.TEXT,
            confidence_threshold=0.9,
            name="Albert Heijn name"
        )
    ]
    
    template_manager.save_template(ah_template)
    print("✅ Albert Heijn template aangemaakt!")
    
    return ah_template

if __name__ == "__main__":
    print("🏪 Maak custom templates voor Nederlandse retailers...")
    print()
    
    mediamarkt = create_mediamarkt_template()
    print()
    albert_heijn = create_albert_heijn_template()
    print()
    
    print("🎯 Templates zijn klaar voor gebruik!")
    print("📋 Bekijk alle templates: python3 -m src.pdf2ubl.cli template list")