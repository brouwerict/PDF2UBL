"""Template manager for storing and managing templates."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from .template_models import Template, FieldPattern, ExtractionMethod, FieldType

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manager for template storage and retrieval."""
    
    def __init__(self, templates_dir: Path = None):
        """Initialize template manager.
        
        Args:
            templates_dir: Directory to store templates (defaults to ./templates)
        """
        self.templates_dir = templates_dir or Path("templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, Template] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load existing templates
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from disk."""
        
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                template = Template.from_dict(template_data)
                self.templates[template.template_id] = template
                
                self.logger.debug(f"Loaded template: {template.name}")
                
            except Exception as e:
                self.logger.error(f"Error loading template from {template_file}: {e}")
    
    def save_template(self, template: Template):
        """Save template to disk."""
        
        template_file = self.templates_dir / f"{template.template_id}.json"
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.templates[template.template_id] = template
            self.logger.info(f"Saved template: {template.name}")
            
        except Exception as e:
            self.logger.error(f"Error saving template {template.template_id}: {e}")
            raise
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def get_default_template(self) -> Optional[Template]:
        """Get the default template (generic_nl)."""
        return self.get_template('generic_nl')
    
    def get_templates(self) -> List[Template]:
        """Get all templates."""
        return list(self.templates.values())
    
    def get_templates_by_supplier(self, supplier_name: str) -> List[Template]:
        """Get templates for specific supplier."""
        
        matching_templates = []
        
        for template in self.templates.values():
            if template.supplier_name and supplier_name.lower() in template.supplier_name.lower():
                matching_templates.append(template)
            
            elif any(alias.lower() in supplier_name.lower() for alias in template.supplier_aliases):
                matching_templates.append(template)
        
        return matching_templates
    
    def find_best_template(self, 
                          raw_text: str,
                          supplier_hint: str = None) -> Optional[Template]:
        """Find best matching template for the given text."""
        
        from .template_engine import TemplateEngine
        
        engine = TemplateEngine()
        best_template = None
        best_score = 0.0
        
        # Filter templates by supplier hint if provided
        candidates = self.templates.values()
        if supplier_hint:
            supplier_templates = self.get_templates_by_supplier(supplier_hint)
            if supplier_templates:
                candidates = supplier_templates
        
        # Test each template (excluding generic_nl initially)
        for template in candidates:
            if template.template_id == 'generic_nl':
                continue  # Skip generic_nl in first pass
                
            matches, confidence = engine.match_supplier(template, raw_text)
            
            self.logger.debug(f"Template '{template.name}': matches={matches}, confidence={confidence:.2f}")
            
            if matches and confidence > best_score:
                best_template = template
                best_score = confidence
                self.logger.debug(f"New best template: {template.name} (confidence: {confidence:.2f})")
        
        # If we found a good template, use it
        if best_template and best_score >= 0.5:
            self.logger.info(f"Selected template: {best_template.name} (confidence: {best_score:.2f})")
            return best_template
        
        # Otherwise, default to generic_nl
        generic_template = self.get_template('generic_nl')
        if generic_template:
            self.logger.info(f"Using default template: generic_nl (no specific match found, best score: {best_score:.2f})")
            return generic_template
        
        return None
    
    def create_template(self, 
                       template_id: str,
                       name: str,
                       supplier_name: str = None,
                       description: str = "") -> Template:
        """Create a new template."""
        
        template = Template(
            template_id=template_id,
            name=name,
            supplier_name=supplier_name,
            description=description
        )
        
        self.templates[template_id] = template
        return template
    
    def delete_template(self, template_id: str):
        """Delete template."""
        
        if template_id in self.templates:
            del self.templates[template_id]
            
            # Remove file
            template_file = self.templates_dir / f"{template_id}.json"
            if template_file.exists():
                template_file.unlink()
                
            self.logger.info(f"Deleted template: {template_id}")
    
    def create_default_templates(self):
        """Create default templates for common suppliers."""
        
        # Generic Dutch invoice template
        generic_template = self.create_template(
            template_id="generic_nl",
            name="Generic Dutch Invoice",
            description="Generic template for Dutch invoices"
        )
        
        # Invoice number patterns
        generic_template.add_field_rule(
            field_name="invoice_number",
            field_type=FieldType.TEXT,
            patterns=[
                FieldPattern(
                    pattern=r'factuur(?:nummer)?[:\s#-]*(\w+)',
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.TEXT,
                    confidence_threshold=0.8,
                    name="Dutch invoice number"
                ),
                FieldPattern(
                    pattern=r'invoice(?:\s+number)?[:\s#-]*(\w+)',
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.TEXT,
                    confidence_threshold=0.7,
                    name="English invoice number"
                )
            ],
            required=True
        )
        
        # Invoice date patterns
        generic_template.add_field_rule(
            field_name="invoice_date",
            field_type=FieldType.DATE,
            patterns=[
                FieldPattern(
                    pattern=r'factuurdatum[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.DATE,
                    confidence_threshold=0.8,
                    name="Dutch invoice date"
                ),
                FieldPattern(
                    pattern=r'datum[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.DATE,
                    confidence_threshold=0.7,
                    name="Date field"
                )
            ],
            required=True
        )
        
        # Total amount patterns
        generic_template.add_field_rule(
            field_name="total_amount",
            field_type=FieldType.AMOUNT,
            patterns=[
                FieldPattern(
                    pattern=r'totaal[:\s]*€?\s*(\d+[.,]\d{2})',
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.AMOUNT,
                    confidence_threshold=0.8,
                    name="Dutch total amount"
                ),
                FieldPattern(
                    pattern=r'total[:\s]*€?\s*(\d+[.,]\d{2})',
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.AMOUNT,
                    confidence_threshold=0.7,
                    name="English total amount"
                )
            ],
            required=True
        )
        
        # VAT number patterns
        generic_template.add_field_rule(
            field_name="supplier_vat_number",
            field_type=FieldType.VAT_NUMBER,
            patterns=[
                FieldPattern(
                    pattern=r'btw[:\s-]*(?:nr|nummer)?[:\s]*([A-Z]{2}\d{9}B\d{2})',
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.VAT_NUMBER,
                    confidence_threshold=0.9,
                    name="Dutch VAT number"
                ),
                FieldPattern(
                    pattern=r'([A-Z]{2}\d{9}B\d{2})',
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.VAT_NUMBER,
                    confidence_threshold=0.7,
                    name="VAT number pattern"
                )
            ]
        )
        
        # Supplier name patterns
        generic_template.add_field_rule(
            field_name="supplier_name",
            field_type=FieldType.TEXT,
            patterns=[
                FieldPattern(
                    pattern=r'^([A-Z][a-z\s]+(?:B\.?V\.?|Ltd\.?|Inc\.?)?)$',
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.TEXT,
                    confidence_threshold=0.5,
                    name="Company name pattern"
                )
            ]
        )
        
        # Add table rules
        generic_template.add_table_rule(
            table_name="line_items",
            header_patterns=[
                r'beschrijving|description',
                r'aantal|quantity',
                r'prijs|price',
                r'bedrag|amount'
            ],
            column_mapping={
                'beschrijving': 'description',
                'description': 'description',
                'aantal': 'quantity',
                'quantity': 'quantity',
                'prijs': 'unit_price',
                'price': 'unit_price',
                'bedrag': 'total_amount',
                'amount': 'total_amount'
            },
            required_columns=['description']
        )
        
        self.save_template(generic_template)
        
        # KPN template example
        kpn_template = self.create_template(
            template_id="kpn_nl",
            name="KPN Netherlands",
            supplier_name="KPN B.V.",
            description="Template for KPN invoices"
        )
        
        # KPN-specific patterns
        kpn_template.supplier_patterns = [
            FieldPattern(
                pattern=r'KPN\s+B\.V\.',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.TEXT,
                confidence_threshold=0.9,
                name="KPN company name"
            )
        ]
        
        kpn_template.supplier_aliases = ["KPN", "Koninklijke PTT Nederland"]
        
        # Copy generic rules
        kpn_template.extraction_rules = generic_template.extraction_rules.copy()
        kpn_template.table_rules = generic_template.table_rules.copy()
        
        self.save_template(kpn_template)
        
        # Ziggo template example
        ziggo_template = self.create_template(
            template_id="ziggo_nl",
            name="Ziggo Netherlands",
            supplier_name="Ziggo B.V.",
            description="Template for Ziggo invoices"
        )
        
        # Ziggo-specific patterns
        ziggo_template.supplier_patterns = [
            FieldPattern(
                pattern=r'Ziggo\s+B\.V\.',
                method=ExtractionMethod.REGEX,
                field_type=FieldType.TEXT,
                confidence_threshold=0.9,
                name="Ziggo company name"
            )
        ]
        
        ziggo_template.supplier_aliases = ["Ziggo"]
        
        # Copy generic rules
        ziggo_template.extraction_rules = generic_template.extraction_rules.copy()
        ziggo_template.table_rules = generic_template.table_rules.copy()
        
        self.save_template(ziggo_template)
        
        self.logger.info("Created default templates")
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get statistics about templates."""
        
        total_templates = len(self.templates)
        suppliers_with_templates = len(set(t.supplier_name for t in self.templates.values() if t.supplier_name))
        
        avg_success_rate = 0.0
        if self.templates:
            avg_success_rate = sum(t.success_rate for t in self.templates.values()) / len(self.templates)
        
        most_used_template = None
        if self.templates:
            most_used_template = max(self.templates.values(), key=lambda t: t.usage_count)
        
        return {
            'total_templates': total_templates,
            'suppliers_with_templates': suppliers_with_templates,
            'average_success_rate': avg_success_rate,
            'most_used_template': most_used_template.name if most_used_template else None,
            'most_used_template_usage': most_used_template.usage_count if most_used_template else 0
        }
    
    def export_templates(self, output_path: Path):
        """Export all templates to a single file."""
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'templates': [template.to_dict() for template in self.templates.values()]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported {len(self.templates)} templates to {output_path}")
    
    def import_templates(self, import_path: Path):
        """Import templates from a file."""
        
        with open(import_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        imported_count = 0
        
        for template_data in import_data.get('templates', []):
            try:
                template = Template.from_dict(template_data)
                self.save_template(template)
                imported_count += 1
                
            except Exception as e:
                self.logger.error(f"Error importing template {template_data.get('template_id', 'unknown')}: {e}")
        
        self.logger.info(f"Imported {imported_count} templates from {import_path}")
        
        return imported_count