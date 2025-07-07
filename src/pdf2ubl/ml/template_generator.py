"""ML-powered template generator for PDF2UBL."""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from ..extractors.pdf_extractor import PDFExtractor
from ..templates.template_models import Template, FieldPattern, ExtractionMethod, FieldType
from ..templates.template_manager import TemplateManager

logger = logging.getLogger(__name__)

@dataclass
class TemplateGenerationResult:
    """Result of template generation."""
    template: Template
    confidence_score: float
    suggested_patterns: List[Dict[str, Any]]
    field_mappings: Dict[str, str]
    supplier_patterns: List[Dict[str, Any]]

@dataclass
class TemplateImprovementResult:
    """Result of template improvement."""
    template: Template
    confidence_score: float
    improvements: List[str]

class TemplateGenerator:
    """ML-powered template generator."""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.logger = logging.getLogger(__name__)
        
        # Common field patterns for Dutch invoices
        self.field_patterns = {
            "invoice_number": [
                r'factuur(?:nummer)?[:\s#-]*([A-Z0-9\-/]{3,20})',
                r'invoice[:\s#-]*([A-Z0-9\-/]{3,20})',
                r'nr[:\s#-]*([A-Z0-9\-/]{3,20})',
                r'number[:\s#-]*([A-Z0-9\-/]{3,20})',
                r'factuurnr[:\s#-]*([A-Z0-9\-/]{3,20})',
                r'fact[:\s#-]*([A-Z0-9\-/]{3,20})',
                r'(\d{6,})',  # Simple long numbers
                r'([A-Z]{1,3}\d{4,})'  # Letter prefix + numbers
            ],
            "invoice_date": [
                r'factuurdatum[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'datum[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'factuur\s*datum[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'invoice\s*date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # Prefer 4-digit years
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{2})'   # But also accept 2-digit
            ],
            "total_amount": [
                r'totaal[:\s]*€?\s*(\d+[.,]\d{2})',
                r'total[:\s]*€?\s*(\d+[.,]\d{2})',
                r'te\s+betalen[:\s]*€?\s*(\d+[.,]\d{2})',
                r'inclusief\s*btw[:\s]*€?\s*(\d+[.,]\d{2})',
                r'incl\.\s*btw[:\s]*€?\s*(\d+[.,]\d{2})',
                r'including\s*vat[:\s]*€?\s*(\d+[.,]\d{2})',
                r'€\s*(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2})\s*€'
            ],
            "net_amount": [
                r'exclusief\s*btw[:\s]*€?\s*(\d+[.,]\d{2})',
                r'excl\.\s*btw[:\s]*€?\s*(\d+[.,]\d{2})',
                r'excluding\s*vat[:\s]*€?\s*(\d+[.,]\d{2})',
                r'netto[:\s]*€?\s*(\d+[.,]\d{2})',
                r'subtotaal[:\s]*€?\s*(\d+[.,]\d{2})',
                r'subtotal[:\s]*€?\s*(\d+[.,]\d{2})'
            ],
            "vat_amount": [
                r'btw[:\s]*€?\s*(\d+[.,]\d{2})',
                r'vat[:\s]*€?\s*(\d+[.,]\d{2})',
                r'btw\s*bedrag[:\s]*€?\s*(\d+[.,]\d{2})',
                r'vat\s*amount[:\s]*€?\s*(\d+[.,]\d{2})',
                r'21%[:\s]*€?\s*(\d+[.,]\d{2})',
                r'19%[:\s]*€?\s*(\d+[.,]\d{2})'
            ],
            "supplier_vat_number": [
                r'btw[:\s-]*(?:nr|nummer)?[:\s]*([A-Z]{2}\d{9}B\d{2})',
                r'vat[:\s-]*(?:nr|number)?[:\s]*([A-Z]{2}\d{9}B\d{2})',
                r'btw-nr[:\s]*([A-Z]{2}\d{9}B\d{2})',
                r'(NL\d{9}B\d{2})',
                r'([A-Z]{2}\d{9}B\d{2})'
            ],
            "supplier_name": [
                r'([A-Z][A-Za-z\s]+(?:B\.V\.|BV|Ltd|Inc|Nederland|Group))',
                r'^([A-Z][A-Za-z\s]{5,40})',  # First line company names
                r'([A-Z][A-Za-z\s]{3,30})'
            ],
            # Note: line_items should not be extracted as a simple field
            # It requires table extraction or complex parsing
        }
        
        # Common supplier detection patterns
        self.supplier_detection_patterns = [
            r'([A-Z][A-Za-z\s]+(?:B\.V\.|BV|Ltd|Inc))',
            r'^([A-Z][a-z\s]+)$',
            r'factuur\s+van[:\s]*([A-Z][a-z\s]+)',
            r'invoice\s+from[:\s]*([A-Z][a-z\s]+)'
        ]
    
    def generate_template(self, 
                         supplier_name: str,
                         template_id: str,
                         sample_pdfs: List[Path],
                         confidence_threshold: float = 0.5) -> TemplateGenerationResult:
        """Generate a template from sample PDFs using ML analysis."""
        
        self.logger.info(f"Generating template for {supplier_name} with {len(sample_pdfs)} samples")
        
        # Extract text from all sample PDFs
        sample_texts = []
        for pdf_path in sample_pdfs:
            try:
                extracted_data = self.pdf_extractor.extract(pdf_path)
                sample_texts.append(extracted_data.raw_text)
            except Exception as e:
                self.logger.warning(f"Failed to extract from {pdf_path}: {e}")
                continue
        
        if not sample_texts:
            raise ValueError("No valid PDF samples could be processed")
        
        # Analyze patterns across samples
        field_patterns = self._analyze_field_patterns(sample_texts)
        supplier_patterns = self._analyze_supplier_patterns(sample_texts, supplier_name)
        
        # Create template
        template = Template(
            template_id=template_id,
            name=f"{supplier_name} (ML Generated)",
            supplier_name=supplier_name,
            description=f"Auto-generated template for {supplier_name} based on {len(sample_texts)} samples",
            created_date=datetime.now(),
            updated_date=datetime.now()
        )
        
        # Add supplier patterns
        template.supplier_patterns = supplier_patterns
        
        # Add field extraction rules
        for field_name, patterns in field_patterns.items():
            if patterns:  # Only add if patterns were found
                field_type = self._get_field_type(field_name)
                template.add_field_rule(
                    field_name=field_name,
                    field_type=field_type,
                    patterns=patterns,
                    required=field_name in ['invoice_number', 'invoice_date', 'total_amount'],
                    min_confidence=confidence_threshold
                )
        
        # Calculate overall confidence
        confidence_score = self._calculate_template_confidence(template, sample_texts)
        
        # Prepare response data
        suggested_patterns = []
        for field_name, patterns in field_patterns.items():
            for pattern in patterns:
                suggested_patterns.append({
                    "field_name": field_name,
                    "pattern": pattern.pattern,
                    "method": pattern.method.value,
                    "confidence": pattern.confidence_threshold,
                    "name": pattern.name
                })
        
        # Create smart field mappings with actual extracted values
        field_mappings = {}
        
        # Try to extract actual values using the patterns we just created
        for field_name, patterns in field_patterns.items():
            best_value = None
            best_confidence = 0.0
            all_candidates = []
            
            # First try fallback extraction which is often more reliable
            fallback_value = self._extract_field_fallback(field_name, sample_texts)
            if fallback_value:
                best_value = fallback_value
                self.logger.info(f"Found {field_name} via fallback: {best_value}")
            else:
                # Try each pattern and collect all valid candidates
                for pattern in patterns:
                    for text in sample_texts:
                        try:
                            matches = re.finditer(pattern.pattern, text, re.IGNORECASE | re.MULTILINE)
                            for match in matches:
                                extracted_value = match.group(1) if match.groups() else match.group(0)
                                # Clean up the extracted value
                                extracted_value = extracted_value.strip()
                                
                                # Simple validation based on field type
                                if self._validate_field_value(field_name, extracted_value):
                                    all_candidates.append((extracted_value, pattern.confidence_threshold))
                                    self.logger.info(f"Pattern match for {field_name}: {extracted_value}")
                        except Exception as e:
                            self.logger.warning(f"Pattern {pattern.pattern} failed for {field_name}: {e}")
                
                # Sort candidates by confidence and pick the best one
                if all_candidates:
                    all_candidates.sort(key=lambda x: x[1], reverse=True)
                    best_value = all_candidates[0][0]
                    best_confidence = all_candidates[0][1]
                    self.logger.info(f"Selected {field_name}: {best_value} (confidence: {best_confidence})")
            
            # Add the field mapping
            if best_value:
                # Special handling for line_items - don't extract as a simple field
                if field_name == 'line_items':
                    # Skip line_items in field mappings, will be handled by table extraction
                    self.logger.info(f"Skipping line_items field mapping - will use table extraction")
                else:
                    field_mappings[field_name] = best_value
            else:
                # Fallback to showing what we're looking for
                if field_name != 'line_items':  # Don't add fallback for line_items
                    field_mappings[field_name] = f"Looking for {field_name.replace('_', ' ')}"
                    self.logger.warning(f"No value found for {field_name}")
        
        supplier_pattern_data = []
        for pattern in supplier_patterns:
            supplier_pattern_data.append({
                "pattern": pattern.pattern,
                "method": pattern.method.value,
                "confidence": pattern.confidence_threshold,
                "name": pattern.name
            })
        
        return TemplateGenerationResult(
            template=template,
            confidence_score=confidence_score,
            suggested_patterns=suggested_patterns,
            field_mappings=field_mappings,
            supplier_patterns=supplier_pattern_data
        )
    
    def analyze_single_pdf(self, 
                          pdf_path: Path,
                          supplier_name: str,
                          template_id: str) -> TemplateGenerationResult:
        """Analyze a single PDF to suggest template patterns."""
        
        # Extract text from PDF
        extracted_data = self.pdf_extractor.extract(pdf_path)
        sample_texts = [extracted_data.raw_text]
        
        # Use the multi-sample method with single sample
        return self.generate_template(supplier_name, template_id, [pdf_path])
    
    def improve_template(self,
                        existing_template: Template,
                        additional_samples: List[Path]) -> TemplateImprovementResult:
        """Improve existing template with additional samples."""
        
        self.logger.info(f"Improving template {existing_template.template_id} with {len(additional_samples)} samples")
        
        # Extract text from additional samples
        sample_texts = []
        for pdf_path in additional_samples:
            try:
                extracted_data = self.pdf_extractor.extract(pdf_path)
                sample_texts.append(extracted_data.raw_text)
            except Exception as e:
                self.logger.warning(f"Failed to extract from {pdf_path}: {e}")
                continue
        
        improvements = []
        
        # Analyze new patterns
        new_field_patterns = self._analyze_field_patterns(sample_texts)
        
        # Compare with existing patterns and suggest improvements
        for field_name, new_patterns in new_field_patterns.items():
            existing_rule = next((rule for rule in existing_template.extraction_rules 
                                if rule.field_name == field_name), None)
            
            if existing_rule:
                # Add new patterns that don't exist
                existing_pattern_strings = [p.pattern for p in existing_rule.patterns]
                for new_pattern in new_patterns:
                    if new_pattern.pattern not in existing_pattern_strings:
                        existing_rule.patterns.append(new_pattern)
                        improvements.append(f"Added new pattern for {field_name}: {new_pattern.pattern}")
            else:
                # Add new field rule
                field_type = self._get_field_type(field_name)
                existing_template.add_field_rule(
                    field_name=field_name,
                    field_type=field_type,
                    patterns=new_patterns,
                    required=field_name in ['invoice_number', 'invoice_date', 'total_amount']
                )
                improvements.append(f"Added new field extraction for {field_name}")
        
        # Update template metadata
        existing_template.updated_date = datetime.now()
        
        # Calculate new confidence
        all_samples = sample_texts  # In real implementation, would include original samples
        confidence_score = self._calculate_template_confidence(existing_template, all_samples)
        
        return TemplateImprovementResult(
            template=existing_template,
            confidence_score=confidence_score,
            improvements=improvements
        )
    
    def extract_supplier_name(self, text: str) -> str:
        """Extract supplier name from PDF text."""
        
        # Try each supplier detection pattern
        for pattern in self.supplier_detection_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 50:  # Reasonable length
                    return name
        
        # Fallback: look for company keywords
        company_patterns = [
            r'([A-Z][a-z\s]+B\.V\.)',
            r'([A-Z][a-z\s]+BV)',
            r'([A-Z][a-z\s]+Ltd\.?)',
            r'([A-Z][a-z\s]+Inc\.?)',
            r'([A-Z][a-z\s]+Nederland)',
            r'([A-Z][a-z\s]+Group)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return "Unknown Supplier"
    
    def _analyze_field_patterns(self, sample_texts: List[str]) -> Dict[str, List[FieldPattern]]:
        """Analyze field patterns across sample texts."""
        
        field_patterns = {}
        
        for field_name, base_patterns in self.field_patterns.items():
            patterns = []
            
            for pattern_str in base_patterns:
                # Test pattern against all samples
                matches = 0
                total_samples = len(sample_texts)
                
                for text in sample_texts:
                    if re.search(pattern_str, text, re.IGNORECASE | re.MULTILINE):
                        matches += 1
                
                # Calculate confidence based on match rate
                confidence = matches / total_samples if total_samples > 0 else 0
                
                # Only include patterns with reasonable confidence
                if confidence >= 0.3:  # At least 30% match rate
                    field_type = self._get_field_type(field_name)
                    method = ExtractionMethod.REGEX
                    
                    pattern = FieldPattern(
                        pattern=pattern_str,
                        method=method,
                        field_type=field_type,
                        confidence_threshold=max(0.5, confidence),
                        name=f"Auto-detected {field_name} pattern",
                        description=f"Pattern found in {matches}/{total_samples} samples"
                    )
                    patterns.append(pattern)
            
            if patterns:
                # Sort by confidence (highest first)
                patterns.sort(key=lambda p: p.confidence_threshold, reverse=True)
                field_patterns[field_name] = patterns[:3]  # Keep top 3 patterns
        
        return field_patterns
    
    def _analyze_supplier_patterns(self, sample_texts: List[str], supplier_name: str) -> List[FieldPattern]:
        """Analyze supplier-specific patterns."""
        
        patterns = []
        
        # Basic supplier name pattern
        escaped_name = re.escape(supplier_name)
        basic_pattern = FieldPattern(
            pattern=escaped_name,
            method=ExtractionMethod.REGEX,
            field_type=FieldType.TEXT,
            confidence_threshold=0.8,
            name=f"{supplier_name} exact match",
            description="Exact supplier name match"
        )
        patterns.append(basic_pattern)
        
        # Look for common variations
        name_parts = supplier_name.split()
        if len(name_parts) > 1:
            # Create pattern with first and last word
            first_last = f"{name_parts[0]}.*{name_parts[-1]}"
            variation_pattern = FieldPattern(
                pattern=first_last,
                method=ExtractionMethod.REGEX,
                field_type=FieldType.TEXT,
                confidence_threshold=0.7,
                name=f"{supplier_name} variation",
                description="Supplier name with variations"
            )
            patterns.append(variation_pattern)
        
        # Look for company-specific identifiers in sample texts
        for text in sample_texts:
            # Find unique identifiers (e.g., addresses, phone numbers)
            unique_patterns = self._find_unique_identifiers(text, supplier_name)
            patterns.extend(unique_patterns)
        
        return patterns[:5]  # Keep top 5 patterns
    
    def _find_unique_identifiers(self, text: str, supplier_name: str) -> List[FieldPattern]:
        """Find unique identifiers for supplier in text."""
        
        patterns = []
        
        # Look for addresses (Dutch postal codes)
        postal_code_matches = re.findall(r'\d{4}\s*[A-Z]{2}', text)
        for postal_code in postal_code_matches:
            pattern = FieldPattern(
                pattern=re.escape(postal_code),
                method=ExtractionMethod.REGEX,
                field_type=FieldType.TEXT,
                confidence_threshold=0.9,
                name=f"{supplier_name} postal code",
                description="Supplier postal code identifier"
            )
            patterns.append(pattern)
        
        # Look for phone numbers
        phone_matches = re.findall(r'[\+\d\s\-\(\)]{10,}', text)
        for phone in phone_matches:
            if len(phone.strip()) >= 10:  # Reasonable phone number length
                pattern = FieldPattern(
                    pattern=re.escape(phone.strip()),
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.TEXT,
                    confidence_threshold=0.8,
                    name=f"{supplier_name} phone",
                    description="Supplier phone number identifier"
                )
                patterns.append(pattern)
        
        # Look for website domains
        domain_matches = re.findall(r'[\w\.-]+\.[a-z]{2,4}', text, re.IGNORECASE)
        for domain in domain_matches:
            if '.' in domain and len(domain) > 4:
                pattern = FieldPattern(
                    pattern=re.escape(domain),
                    method=ExtractionMethod.REGEX,
                    field_type=FieldType.TEXT,
                    confidence_threshold=0.7,
                    name=f"{supplier_name} domain",
                    description="Supplier domain identifier"
                )
                patterns.append(pattern)
        
        return patterns[:3]  # Keep top 3 unique identifiers
    
    def _get_field_type(self, field_name: str) -> FieldType:
        """Get appropriate field type for field name."""
        
        type_mapping = {
            "invoice_number": FieldType.TEXT,
            "invoice_date": FieldType.DATE,
            "total_amount": FieldType.AMOUNT,
            "net_amount": FieldType.AMOUNT,
            "vat_amount": FieldType.AMOUNT,
            "supplier_name": FieldType.TEXT,
            "supplier_vat_number": FieldType.VAT_NUMBER,
            "supplier_address": FieldType.TEXT,
            "supplier_phone": FieldType.PHONE,
            "supplier_email": FieldType.EMAIL,
            "customer_name": FieldType.TEXT,
            "customer_address": FieldType.TEXT,
            "currency": FieldType.TEXT,
            "due_date": FieldType.DATE,
            "payment_reference": FieldType.TEXT,
            "line_items": FieldType.TEXT
        }
        
        return type_mapping.get(field_name, FieldType.TEXT)
    
    def _calculate_template_confidence(self, template: Template, sample_texts: List[str]) -> float:
        """Calculate overall confidence score for template."""
        
        if not sample_texts:
            return 0.0
        
        total_score = 0.0
        total_tests = 0
        
        # Test each extraction rule against samples
        for rule in template.extraction_rules:
            for pattern in rule.patterns:
                matches = 0
                for text in sample_texts:
                    if re.search(pattern.pattern, text, re.IGNORECASE | re.MULTILINE):
                        matches += 1
                
                match_rate = matches / len(sample_texts)
                total_score += match_rate * pattern.confidence_threshold
                total_tests += 1
        
        # Test supplier patterns
        for pattern in template.supplier_patterns:
            matches = 0
            for text in sample_texts:
                if re.search(pattern.pattern, text, re.IGNORECASE | re.MULTILINE):
                    matches += 1
            
            match_rate = matches / len(sample_texts)
            total_score += match_rate * pattern.confidence_threshold
            total_tests += 1
        
        return total_score / total_tests if total_tests > 0 else 0.0

    def _validate_field_value(self, field_name: str, value: str) -> bool:
        """Validate if extracted value makes sense for the field type."""
        if not value or len(value.strip()) == 0:
            return False
        
        value = value.strip()
        
        # Basic validation rules
        if field_name == 'invoice_number':
            # Should contain alphanumeric chars, not be too long, not be common words
            if len(value) > 50 or len(value) < 3:
                return False
            # Exclude common false positives - expanded list
            false_positives = [
                'factuur', 'invoice', 'nummer', 'number', 'datum', 'date', 'totaal', 'total', 
                'btw', 'vat', 'brouwer', 'bedrag', 'amount', 'euro', 'eur', 'incl', 'excl',
                'per', 'van', 'from', 'to', 'aan', 'subtotaal', 'subtotal', 'klant', 
                'customer', 'leverancier', 'supplier', 'adres', 'address', 'klantnummer'
            ]
            if value.lower() in false_positives:
                return False
            # Reject if it's just numbers that look like dates or amounts
            if re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', value):
                return False
            if re.match(r'^\d+[.,]\d{2}$', value):
                return False
            # Accept 6-digit numbers (common invoice format like 240879)
            if re.match(r'^\d{6}$', value):
                return True
            # Accept alphanumeric patterns
            if re.match(r'^[A-Z0-9\-/]{3,20}$', value):
                return True
            return True
            
        elif field_name == 'supplier_name':
            # Should be reasonable length, not be amount-like
            if len(value) > 100 or len(value) < 3:
                return False
            # Exclude amounts and common false positives
            if re.match(r'^\d+[.,]\d+$', value) or re.match(r'^[€$]\s*\d+', value):
                return False
            false_positives = [
                'totaal', 'total', 'subtotaal', 'btw', 'vat', 'factuur', 'invoice',
                'bedrag', 'amount', 'datum', 'date', 'nummer', 'number', 'klant',
                'customer', 'inc', 'incl', 'excl', 'per', 'van', 'from', 'to', 'aan'
            ]
            if value.lower() in false_positives:
                return False
            # Must contain at least one letter
            if not re.search(r'[a-zA-Z]', value):
                return False
            return True
            
        elif field_name in ['total_amount', 'net_amount', 'vat_amount']:
            # Should look like an amount
            clean_value = value.replace(' ', '').replace('€', '').replace('$', '').replace(',', '.')
            return bool(re.match(r'^\d+\.\d{2}$', clean_value))
            
        elif field_name == 'invoice_date':
            # Should look like a date
            return bool(re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', value))
            
        elif field_name == 'supplier_vat_number':
            # Should look like a VAT number
            return bool(re.match(r'[A-Z]{2}\d{9}[A-Z]\d{2}|NL\d{9}B\d{2}', value))
            
        elif field_name == 'line_items':
            # Should contain "factuurregels" or be a line with amount
            return 'factuurregels' in value.lower() or (len(value) > 5 and '€' in value)
        
        return True  # Default: accept if no specific rules

    def _extract_field_fallback(self, field_name: str, sample_texts: List[str]) -> Optional[str]:
        """Fallback extraction when regex patterns don't work."""
        
        for text in sample_texts:
            if field_name == 'invoice_number':
                # Look for factuurnummer specifically in text
                lines = text.split('\n')
                for line in lines:
                    if 'factuurnummer' in line.lower():
                        # Extract number after factuurnummer
                        match = re.search(r'factuurnummer[:\s]*(\d+)', line, re.IGNORECASE)
                        if match:
                            number = match.group(1)
                            if self._validate_field_value(field_name, number):
                                return number
                
                # Look for common invoice number patterns
                patterns = [
                    r'factuurnummer[:\s]*(\d+)',
                    r'(\d{6})',  # Exactly 6 digits like 240879
                    r'([A-Z]{1,3}\d{4,})',  # Letters followed by 4+ digits
                    r'(\d{4,}[A-Z]+)',  # 4+ digits followed by letters
                    r'([A-Z]+\d+[A-Z]*\d*)'  # Mixed alphanumeric
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        if self._validate_field_value(field_name, match):
                            return match
            
            elif field_name == 'supplier_name':
                # Look for company names in first few lines
                lines = text.split('\n')[:15]  # First 15 lines
                for line in lines:
                    line = line.strip()
                    # Skip obvious non-company lines
                    if any(skip in line.lower() for skip in ['klantnummer', 'factuurnummer', 'factuurdatum', 'aantal', 'omschrijving', 'prijs']):
                        continue
                    
                    # Look for company indicators
                    if any(indicator in line.upper() for indicator in ['ICT', 'HOSTING', 'B.V.', 'BV', 'LTD', 'INC', 'NEDERLAND', 'GROUP']):
                        if self._validate_field_value(field_name, line):
                            return line
                    
                    # Look for capitalized words that could be company names
                    words = line.split()
                    if len(words) >= 2 and len(line) > 8 and len(line) < 60:
                        # Check if it looks like a company name (multiple capitalized words)
                        cap_words = [w for w in words if w and w[0].isupper() and w.isalpha()]
                        if len(cap_words) >= 2:
                            if self._validate_field_value(field_name, line):
                                return line
            
            elif field_name in ['total_amount', 'net_amount', 'vat_amount']:
                # Look for specific amount indicators first
                lines = text.split('\n')
                
                if field_name == 'total_amount':
                    # Look for total indicators
                    for line in lines:
                        if any(indicator in line.lower() for indicator in ['totaal', 'total', 'te betalen', 'inclusief']):
                            match = re.search(r'€\s*(\d+[.,]\d{2})', line)
                            if match:
                                amount = match.group(1).replace(',', '.')
                                if self._validate_field_value(field_name, amount):
                                    return amount
                
                elif field_name == 'net_amount':
                    # Look for subtotal/net indicators
                    for line in lines:
                        if any(indicator in line.lower() for indicator in ['excl', 'exclusief', 'subtotaal', 'netto']):
                            match = re.search(r'€\s*(\d+[.,]\d{2})', line)
                            if match:
                                amount = match.group(1).replace(',', '.')
                                if self._validate_field_value(field_name, amount):
                                    return amount
                
                elif field_name == 'vat_amount':
                    # Look for BTW indicators
                    for line in lines:
                        if any(indicator in line.lower() for indicator in ['btw', 'vat']) and '€' in line:
                            match = re.search(r'€\s*(\d+[.,]\d{2})', line)
                            if match:
                                amount = match.group(1).replace(',', '.')
                                if self._validate_field_value(field_name, amount):
                                    return amount
                
                # Fallback: Look for amounts in typical formats
                patterns = [
                    r'€\s*(\d+[.,]\d{2})',
                    r'(\d+[.,]\d{2})\s*€',
                    r'(\d+[.,]\d{2})',
                ]
                amounts = []
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        clean_match = match.replace(',', '.')
                        try:
                            amount_val = float(clean_match)
                            if amount_val > 1.0:  # Ignore very small amounts
                                amounts.append(amount_val)
                        except:
                            continue
                
                if amounts:
                    # For total_amount, pick the largest
                    if field_name == 'total_amount':
                        best_amount = max(amounts)
                        return f"{best_amount:.2f}"
                    # For net_amount, pick second largest (often net amount is smaller than total)
                    elif field_name == 'net_amount':
                        sorted_amounts = sorted(set(amounts), reverse=True)
                        if len(sorted_amounts) > 1:
                            return f"{sorted_amounts[1]:.2f}"
                        else:
                            return f"{sorted_amounts[0]:.2f}"
                    # For vat_amount, pick the smallest reasonable amount
                    elif field_name == 'vat_amount':
                        reasonable_amounts = [a for a in amounts if a > 1.0 and a < max(amounts) * 0.5]
                        if reasonable_amounts:
                            return f"{min(reasonable_amounts):.2f}"
                        else:
                            return f"{min(amounts):.2f}"
            
            elif field_name == 'invoice_date':
                # Look for factuurdatum specifically first
                lines = text.split('\n')
                for line in lines:
                    if 'factuurdatum' in line.lower():
                        # Extract date after factuurdatum
                        match = re.search(r'factuurdatum[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', line, re.IGNORECASE)
                        if match:
                            date = match.group(1)
                            if self._validate_field_value(field_name, date):
                                return date
                
                # Look for date patterns
                patterns = [
                    r'factuurdatum[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                    r'(\d{2}[-/]\d{2}[-/]\d{4})',  # DD-MM-YYYY like 02-01-2024
                    r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                    r'(\d{1,2}[-/]\d{1,2}[-/]\d{2})',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        if self._validate_field_value(field_name, match):
                            return match
            
            elif field_name == 'supplier_vat_number':
                # Look for VAT number patterns
                patterns = [
                    r'(NL\d{9}B\d{2})',
                    r'([A-Z]{2}\d{9}[A-Z]\d{2})'
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        if self._validate_field_value(field_name, match):
                            return match
            
            elif field_name == 'line_items':
                # Count probable line items
                lines = text.split('\n')
                line_item_count = 0
                for line in lines:
                    line = line.strip()
                    # Look for lines with description and amount
                    if len(line) > 10 and '€' in line and re.search(r'\d+[.,]\d{2}', line):
                        # Exclude header/footer lines
                        if not any(header in line.lower() for header in ['totaal', 'total', 'btw', 'vat', 'factuur', 'invoice']):
                            line_item_count += 1
                
                if line_item_count > 0:
                    return f"{line_item_count} factuurregels"
        
        return None