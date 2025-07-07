"""Template engine for supplier-specific extraction."""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal

from ..extractors.pdf_extractor import ExtractedInvoiceData
from ..extractors.text_extractor import TextExtractor
from ..extractors.table_extractor import TableExtractor
from .template_models import Template, FieldPattern, ExtractionRule, ExtractionMethod, FieldType

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Engine for applying templates to extract invoice data."""
    
    def __init__(self):
        self.text_extractor = TextExtractor()
        self.table_extractor = TableExtractor()
        self.logger = logging.getLogger(__name__)
    
    def apply_template(self, 
                      template: Template,
                      raw_text: str,
                      tables: List[List[List[str]]] = None,
                      positioned_text: Dict[str, Any] = None) -> ExtractedInvoiceData:
        """Apply template to extract invoice data.
        
        Args:
            template: Template to apply
            raw_text: Raw text from PDF
            tables: Extracted tables
            positioned_text: Text with positioning information
            
        Returns:
            ExtractedInvoiceData with extracted information
        """
        
        self.logger.info(f"Applying template: {template.name}")
        
        # Initialize extracted data
        data = ExtractedInvoiceData()
        data.raw_text = raw_text
        data.extraction_method = f"template:{template.template_id}"
        
        # Apply field extraction rules
        for rule in template.extraction_rules:
            field_value, confidence = self._extract_field(rule, raw_text, positioned_text)
            
            if field_value is not None:
                # Store extracted value
                setattr(data, rule.field_name, field_value)
                data.confidence_scores[rule.field_name] = confidence
                
                self.logger.debug(f"Extracted {rule.field_name}: {field_value} (confidence: {confidence:.2f})")
        
        # Apply table extraction rules
        if tables:
            extracted_tables = self.table_extractor.extract_tables(tables)
            
            for table_rule in template.table_rules:
                table_data = self._extract_table_data(table_rule, extracted_tables)
                
                if table_rule.table_name == 'line_items':
                    data.line_items = table_data
                elif table_rule.table_name == 'summary':
                    self._update_summary_data(data, table_data)
        
        # If no line items found in tables, try text parsing
        if not data.line_items:
            data.line_items = self._extract_line_items_from_text(raw_text)
        
        # Apply post-processing
        self._post_process_data(data, template)
        
        return data
    
    def _extract_field(self, 
                      rule: ExtractionRule,
                      raw_text: str,
                      positioned_text: Dict[str, Any] = None) -> Tuple[Optional[Any], float]:
        """Extract field value using extraction rule."""
        
        best_value = None
        best_confidence = 0.0
        
        # Try each pattern in order of priority
        sorted_patterns = sorted(rule.patterns, key=lambda p: p.priority, reverse=True)
        
        for pattern in sorted_patterns:
            value, confidence = self._apply_pattern(pattern, raw_text, positioned_text)
            
            if value is not None and confidence > best_confidence:
                best_value = value
                best_confidence = confidence
                
                # If we have a high confidence match, we can stop
                if confidence > 0.9:
                    break
        
        # Try fallback patterns if no good match found
        if best_confidence < rule.min_confidence and rule.fallback_patterns:
            for pattern in rule.fallback_patterns:
                value, confidence = self._apply_pattern(pattern, raw_text, positioned_text)
                
                if value is not None and confidence > best_confidence:
                    best_value = value
                    best_confidence = confidence
        
        # Use default value if no match found
        if best_value is None and rule.default_value is not None:
            best_value = rule.default_value
            best_confidence = 0.1
        
        # Convert to appropriate type
        if best_value is not None:
            best_value = self._convert_field_type(best_value, rule.field_type)
            
            # Special handling for supplier names
            if rule.field_name == 'supplier_name' and best_value:
                if best_value.lower() == 'vdx':
                    best_value = 'VDX'
        
        return best_value, best_confidence
    
    def _apply_pattern(self, 
                      pattern: FieldPattern,
                      raw_text: str,
                      positioned_text: Dict[str, Any] = None) -> Tuple[Optional[Any], float]:
        """Apply single pattern to extract value."""
        
        if pattern.method == ExtractionMethod.REGEX:
            return self._apply_regex_pattern(pattern, raw_text)
        
        elif pattern.method == ExtractionMethod.KEYWORD:
            return self._apply_keyword_pattern(pattern, raw_text)
        
        elif pattern.method == ExtractionMethod.POSITION:
            return self._apply_position_pattern(pattern, positioned_text)
        
        else:
            self.logger.warning(f"Unsupported extraction method: {pattern.method}")
            return None, 0.0
    
    def _apply_regex_pattern(self, pattern: FieldPattern, text: str) -> Tuple[Optional[str], float]:
        """Apply regex pattern to extract value."""
        
        flags = 0
        if not pattern.case_sensitive:
            flags |= re.IGNORECASE
        if pattern.multiline:
            flags |= re.MULTILINE
        
        try:
            if pattern.whole_word:
                # Add word boundaries
                regex_pattern = r'\b' + pattern.pattern + r'\b'
            else:
                regex_pattern = pattern.pattern
            
            match = re.search(regex_pattern, text, flags)
            
            if match:
                # Extract value (use first group if available, otherwise full match)
                value = match.group(1) if match.groups() else match.group(0)
                
                # Apply cleanup if specified
                if pattern.cleanup_pattern:
                    value = re.sub(pattern.cleanup_pattern, '', value)
                
                # Apply replacement if specified
                if pattern.replacement_pattern:
                    value = re.sub(pattern.pattern, pattern.replacement_pattern, value)
                
                # Validate if validation pattern is provided
                if pattern.validation_pattern:
                    if not re.match(pattern.validation_pattern, value):
                        return None, 0.0
                
                # Check context requirements
                if pattern.required_context:
                    if not self._check_context(text, match.start(), pattern.required_context, True):
                        return None, 0.0
                
                if pattern.forbidden_context:
                    if self._check_context(text, match.start(), pattern.forbidden_context, False):
                        return None, 0.0
                
                # Calculate confidence based on pattern specificity
                confidence = self._calculate_pattern_confidence(pattern, value, match)
                
                return value.strip(), confidence
            
        except re.error as e:
            self.logger.error(f"Regex error in pattern '{pattern.pattern}': {e}")
        
        return None, 0.0
    
    def _apply_keyword_pattern(self, pattern: FieldPattern, text: str) -> Tuple[Optional[str], float]:
        """Apply keyword-based pattern to extract value."""
        
        # Find keyword in text
        keywords = pattern.pattern.split('|')
        
        for keyword in keywords:
            keyword = keyword.strip()
            
            # Search for keyword (case-insensitive unless specified)
            if pattern.case_sensitive:
                keyword_pos = text.find(keyword)
            else:
                keyword_pos = text.lower().find(keyword.lower())
            
            if keyword_pos != -1:
                # Extract value after keyword
                after_keyword = text[keyword_pos + len(keyword):].strip()
                
                # Look for value pattern after keyword
                value_patterns = [
                    r'^[:\s]*([^\n\r]+)',  # Value on same line
                    r'^[:\s]*\n([^\n\r]+)',  # Value on next line
                ]
                
                for value_pattern in value_patterns:
                    match = re.match(value_pattern, after_keyword)
                    if match:
                        value = match.group(1).strip()
                        
                        # Clean up common separators
                        value = re.sub(r'^[:\-\s]+', '', value)
                        value = re.sub(r'[:\-\s]+$', '', value)
                        
                        if value:
                            confidence = pattern.confidence_threshold
                            return value, confidence
        
        return None, 0.0
    
    def _apply_position_pattern(self, 
                               pattern: FieldPattern,
                               positioned_text: Dict[str, Any]) -> Tuple[Optional[str], float]:
        """Apply position-based pattern to extract value."""
        
        if not positioned_text:
            return None, 0.0
        
        # This would require positioned text data from PDF extraction
        # For now, return None (to be implemented with proper positioned text data)
        return None, 0.0
    
    def _check_context(self, text: str, position: int, context_patterns: List[str], required: bool) -> bool:
        """Check if context patterns are present around the match position."""
        
        # Define context window (e.g., 100 characters before and after)
        context_window = 100
        start_pos = max(0, position - context_window)
        end_pos = min(len(text), position + context_window)
        context_text = text[start_pos:end_pos]
        
        for context_pattern in context_patterns:
            pattern_found = bool(re.search(context_pattern, context_text, re.IGNORECASE))
            
            if required and not pattern_found:
                return False
            elif not required and pattern_found:
                return True
        
        return required  # If required=True, all patterns were found; if required=False, no patterns were found
    
    def _calculate_pattern_confidence(self, pattern: FieldPattern, value: str, match: re.Match) -> float:
        """Calculate confidence score for pattern match."""
        
        confidence = pattern.confidence_threshold
        
        # Adjust confidence based on pattern specificity
        if len(pattern.pattern) > 10:  # More specific patterns get higher confidence
            confidence += 0.1
        
        # Adjust confidence based on value quality
        if pattern.field_type == FieldType.AMOUNT:
            if re.match(r'^\d+[.,]\d{2}$', value):  # Proper amount format
                confidence += 0.2
        
        elif pattern.field_type == FieldType.DATE:
            if re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', value):  # Proper date format
                confidence += 0.2
        
        elif pattern.field_type == FieldType.VAT_NUMBER:
            if re.match(r'^[A-Z]{2}\d{9}B\d{2}$', value):  # Proper VAT format
                confidence += 0.3
        
        # Adjust confidence based on match position
        if match.start() < 1000:  # Early in document (likely header info)
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _convert_field_type(self, value: Any, field_type: FieldType) -> Any:
        """Convert extracted value to appropriate type."""
        
        if value is None:
            return None
        
        try:
            if field_type == FieldType.NUMBER:
                return self._parse_numeric_value(str(value))
            
            elif field_type == FieldType.AMOUNT:
                return self._parse_numeric_value(str(value), remove_currency=True)
            
            elif field_type == FieldType.PERCENTAGE:
                percent_str = str(value).replace('%', '').replace(',', '.')
                return float(percent_str)
            
            elif field_type == FieldType.DATE:
                # Try to parse date
                date_str = str(value)
                
                # Handle Dutch month names
                dutch_months = {
                    'januari': 'January', 'februari': 'February', 'maart': 'March',
                    'april': 'April', 'mei': 'May', 'juni': 'June',
                    'juli': 'July', 'augustus': 'August', 'september': 'September',
                    'oktober': 'October', 'november': 'November', 'december': 'December'
                }
                
                # Replace Dutch month names with English for parsing
                date_str_en = date_str
                for dutch, english in dutch_months.items():
                    date_str_en = date_str_en.replace(dutch, english)
                
                # Try various date formats
                for fmt in ['%d %B %Y', '%d.%m.%Y', '%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y', '%Y-%m-%d']:
                    try:
                        return datetime.strptime(date_str_en, fmt)
                    except ValueError:
                        continue
                return value  # Return as string if parsing fails
            
            else:
                return str(value)
                
        except (ValueError, TypeError):
            return value
    
    def _parse_numeric_value(self, value_str: str, remove_currency: bool = False) -> Optional[float]:
        """Parse numeric value handling various formats including thousands separators."""
        try:
            cleaned = value_str.strip()
            
            # Remove currency symbols if requested
            if remove_currency:
                cleaned = re.sub(r'[€$£¥\s]', '', cleaned)
            
            # Handle different number formats
            if ',' in cleaned and '.' in cleaned:
                # Both comma and dot present
                # Assume last comma/dot is decimal separator
                if cleaned.rfind(',') > cleaned.rfind('.'):
                    # Comma is decimal separator (European format)
                    # e.g., "1.120,60" -> "1120.60"
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    # Dot is decimal separator (US format)
                    # e.g., "1,120.60" -> "1120.60"
                    cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Only comma present - could be thousands or decimal
                comma_parts = cleaned.split(',')
                if len(comma_parts) == 2 and len(comma_parts[1]) <= 2:
                    # Decimal separator (e.g., "1120,60")
                    cleaned = cleaned.replace(',', '.')
                else:
                    # Thousands separator (e.g., "1,120")
                    cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
    
    def _extract_table_data(self, 
                           table_rule,
                           extracted_tables: List) -> List[Dict[str, Any]]:
        """Extract data from tables using table rule."""
        
        # Find matching table
        matching_table = None
        for table in extracted_tables:
            if self._table_matches_rule(table, table_rule):
                matching_table = table
                break
        
        if not matching_table:
            return []
        
        # Extract data from matching table
        table_data = []
        
        if table_rule.table_name == 'line_items':
            table_data = self.table_extractor.extract_line_items([matching_table])
        elif table_rule.table_name == 'summary':
            summary_data = self.table_extractor.extract_summary_data([matching_table])
            table_data = [summary_data] if summary_data else []
        
        return table_data
    
    def _table_matches_rule(self, table, table_rule) -> bool:
        """Check if table matches the table rule."""
        
        if not table.headers:
            return False
        
        # Check if any header pattern matches
        for header_pattern in table_rule.header_patterns:
            for header in table.headers:
                if re.search(header_pattern, header, re.IGNORECASE):
                    return True
        
        return False
    
    def _update_summary_data(self, data: ExtractedInvoiceData, summary_data: List[Dict[str, Any]]):
        """Update invoice data with summary information."""
        
        if not summary_data:
            return
        
        summary = summary_data[0]
        
        if 'subtotal' in summary and summary['subtotal']:
            data.net_amount = summary['subtotal']
        
        if 'vat_amount' in summary and summary['vat_amount']:
            data.vat_amount = summary['vat_amount']
        
        if 'total_amount' in summary and summary['total_amount']:
            data.total_amount = summary['total_amount']
    
    def _post_process_data(self, data: ExtractedInvoiceData, template: Template):
        """Post-process extracted data using template settings."""
        
        # Apply template-specific formatting
        if template.decimal_separator == ',':
            # Convert decimal separators if needed
            for field in ['total_amount', 'vat_amount', 'net_amount']:
                value = getattr(data, field, None)
                if value and isinstance(value, str):
                    converted_value = self._parse_numeric_value(value, remove_currency=True)
                    if converted_value is not None:
                        setattr(data, field, converted_value)
        
        # Set currency
        if not data.currency:
            data.currency = template.currency
        
        # Calculate missing amounts
        if data.total_amount and data.vat_amount and not data.net_amount:
            data.net_amount = data.total_amount - data.vat_amount
        
        elif data.net_amount and data.vat_amount and not data.total_amount:
            data.total_amount = data.net_amount + data.vat_amount
    
    def match_supplier(self, template: Template, raw_text: str) -> Tuple[bool, float]:
        """Check if template matches the supplier in the text."""
        
        best_confidence = 0.0
        
        # First check direct supplier name and aliases in text
        text_lower = raw_text.lower()
        
        if template.supplier_name:
            supplier_lower = template.supplier_name.lower()
            if supplier_lower in text_lower:
                best_confidence = max(best_confidence, 0.8)
                self.logger.debug(f"Found supplier name '{template.supplier_name}' in text")
        
        for alias in template.supplier_aliases:
            alias_lower = alias.lower()
            if alias_lower in text_lower:
                best_confidence = max(best_confidence, 0.7)
                self.logger.debug(f"Found supplier alias '{alias}' in text")
        
        # Then check specific supplier patterns
        if template.supplier_patterns:
            for pattern in template.supplier_patterns:
                value, confidence = self._apply_pattern(pattern, raw_text)
                
                if value and confidence > best_confidence:
                    best_confidence = confidence
                    self.logger.debug(f"Supplier pattern matched: '{pattern.name}' with confidence {confidence}")
                    
                    # Boost confidence if value matches known names
                    if template.supplier_name:
                        if template.supplier_name.lower() in value.lower():
                            best_confidence += 0.3
                    
                    for alias in template.supplier_aliases:
                        if alias.lower() in value.lower():
                            best_confidence += 0.2
        
        # If no patterns but we found name/alias, still return positive
        if not template.supplier_patterns and best_confidence > 0:
            self.logger.debug(f"No supplier patterns but found name/alias with confidence {best_confidence}")
        
        match_found = best_confidence > 0.5
        final_confidence = min(best_confidence, 1.0)
        
        if match_found:
            self.logger.info(f"Template '{template.name}' matches with confidence {final_confidence:.2f}")
        
        return match_found, final_confidence
    
    def get_extraction_quality(self, data: ExtractedInvoiceData, template: Template) -> float:
        """Calculate extraction quality score."""
        
        scores = []
        
        # Check required fields
        for rule in template.extraction_rules:
            if rule.required:
                field_value = getattr(data, rule.field_name, None)
                if field_value is not None:
                    confidence = data.confidence_scores.get(rule.field_name, 0.0)
                    scores.append(confidence)
                else:
                    scores.append(0.0)
        
        # Check overall confidence
        if data.confidence_scores:
            avg_confidence = sum(data.confidence_scores.values()) / len(data.confidence_scores)
            scores.append(avg_confidence)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _extract_line_items_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract line items from invoice text when no table structure is found."""
        
        line_items = []
        lines = text.split('\n')
        
        # First pass: Regular pattern (description € amount on same line)
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and non-relevant lines
            if not line:
                continue
                
            # Skip header/summary lines
            skip_keywords = [
                'FACTUUR', 'Factuurnummer', 'Factuurdatum', 'Accountnaam',
                'Subtotaal', 'BTW', 'Totaal', 'te betalen', 'machtiging',
                'KvK:', 'IBAN:', 'BIC:', 'BIJLAGE', 'PRODUCT', 'PERIODE'
            ]
            
            if any(keyword in line for keyword in skip_keywords):
                continue
            
            # Look for line item pattern: description € amount
            pattern = r'^(.+?)\s*€\s*(\d+[.,]\d{2})$'
            match = re.match(pattern, line)
            
            if match:
                description = match.group(1).strip()
                amount_str = match.group(2)
                amount = self._parse_numeric_value(amount_str, remove_currency=True)
                if amount is None:
                    continue
                
                # Filter for actual line items (services/products)
                line_item_keywords = [
                    'filter', 'domeinnamen', 'domein', '.nl', '.com', 
                    'hosting', 'service', 'onderhoud', 'support',
                    'cloud', 'harddrive', 'account', 'licenties', 'sof-'
                ]
                
                if any(keyword in description.lower() for keyword in line_item_keywords):
                    line_items.append({
                        'description': description,
                        'quantity': 1,
                        'unit_price': amount,
                        'total_amount': amount
                    })
                    
                    self.logger.debug(f"Extracted line item from text: {description} - €{amount:.2f}")
        
        # Second pass: VDX-style patterns (product code before description)
        if 'VDX' in text or 'vdx' in text or 'SOF-' in text:
            vdx_items = self._extract_vdx_line_items(lines)
            if vdx_items:
                # VDX items are complete, return only these
                return vdx_items
        
        # Dustin-style patterns (structured product lines)
        if 'Dustin' in text or 'BON Pg' in text:
            dustin_items = self._extract_dustin_line_items(lines)
            if dustin_items:
                line_items.extend(dustin_items)
        
        # DectDirect-style patterns
        if 'DectDirect' in text or 'Ubiquiti' in text:
            dectdirect_items = self._extract_dectdirect_line_items(lines)
            if dectdirect_items:
                line_items.extend(dectdirect_items)
        
        # Opslagruimte-style patterns
        if 'Opslagruimte' in text or 'opslagruimte' in text:
            opslagruimte_items = self._extract_opslagruimte_line_items(lines)
            if opslagruimte_items:
                line_items.extend(opslagruimte_items)
        
        # 123accu-style patterns
        if '123accu' in text or 'ABS00' in text or 'AMS00' in text:
            accu_items = self._extract_123accu_line_items(lines)
            if accu_items:
                line_items.extend(accu_items)
        
        # WeServit-style patterns
        if 'weservit' in text.lower() or 'weservcloud' in text.lower():
            weservit_items = self._extract_weservit_line_items(lines)
            if weservit_items:
                line_items.extend(weservit_items)
        
        # Coolblue-style patterns
        if 'Coolblue' in text or 'coolblue' in text.lower():
            coolblue_items = self._extract_coolblue_line_items(lines)
            if coolblue_items:
                line_items.extend(coolblue_items)
        
        # Third pass: Proserve-style patterns (structured line items)
        if 'Proserve' in text or 'proserve' in text:
            proserve_items = self._extract_proserve_line_items(lines)
            if proserve_items:
                # Replace existing items with Proserve-specific ones
                line_items = proserve_items
        
        self.logger.info(f"Extracted {len(line_items)} line items from text")
        return line_items
    
    def _extract_vdx_line_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract VDX-specific line items where product code comes before description."""
        
        vdx_items = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for VDX product lines: SOF-CHR-101 5 0 € 4,35 € 21,75
            # Format: PRODUCT_CODE QUANTITY MONTHS € PRICE_PER_UNIT € TOTAL
            vdx_pattern = r'^(SOF-[A-Z]+-\d+)\s+(\d+)\s+\d+\s+€\s+([\d,.-]+)\s+€\s+([\d,.-]+)$'
            match = re.search(vdx_pattern, line)
            
            if match:
                product_code = match.group(1)
                quantity_str = match.group(2)
                unit_price_str = match.group(3).replace(',', '.')
                total_amount_str = match.group(4).replace(',', '.')
                
                quantity = float(quantity_str)
                unit_price = float(unit_price_str.replace('-', '0'))
                total_amount = float(total_amount_str.replace('-', '0'))
                
                # Only process items with non-zero amounts
                if total_amount > 0:
                    # Look for description in the next line
                    description = product_code  # Default to product code
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # Check if next line is a description (not another product code)
                        if 'SOF-' not in next_line and not re.match(r'^\d+\s+\d+\s+€', next_line):
                            description = next_line
                    
                    # Create full description with product code
                    full_description = f"{description} ({product_code})"
                    
                    vdx_items.append({
                        'description': full_description,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_amount': total_amount
                    })
                    
                    self.logger.debug(f"Extracted VDX line item: {full_description} - {quantity}x €{unit_price:.2f} = €{total_amount:.2f}")
            
            i += 1
        
        return vdx_items
    
    def _extract_proserve_line_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract Proserve-specific line items from structured table format."""
        
        proserve_items = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for Proserve line items with structured format
            # Format: "Hosted Exchange Standard Mailbox - per user april 2025 2 € 6,59 € 13,18"
            proserve_pattern = r'^(.+?)\s+(\d{4})\s+(\d+)\s+€\s+([\d,.-]+)\s+€\s+([\d,.-]+)$'
            match = re.match(proserve_pattern, line)
            
            if match:
                description = match.group(1).strip()
                year = match.group(2)
                quantity = int(match.group(3))
                unit_price_str = match.group(4)
                total_amount_str = match.group(5)
                
                unit_price = self._parse_numeric_value(unit_price_str, remove_currency=True)
                total_amount = self._parse_numeric_value(total_amount_str, remove_currency=True)
                
                if unit_price is None or total_amount is None:
                    continue
                
                # Add year context to description
                full_description = f"{description} {year}"
                
                proserve_items.append({
                    'description': full_description,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_amount': total_amount
                })
                
                self.logger.debug(f"Extracted Proserve line item: {full_description} - {quantity}x €{unit_price:.2f} = €{total_amount:.2f}")
            
            # Skip simple patterns for Proserve - use structured format only
            # This avoids duplicate extraction of "Hosted Exchange € 13,18"
            elif False:  # Disabled to prevent duplicates
                pass
        
        return proserve_items
    
    def _extract_dustin_line_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract Dustin-specific line items from structured format."""
        
        dustin_items = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for lines starting with article number (10 digits)
            article_start_pattern = r'^(\d{10})\s+(.+)'
            match = re.match(article_start_pattern, line)
            
            if match:
                artikel_nummer = match.group(1)
                rest_of_line = match.group(2).strip()
                
                # Try to extract numbers from end of line (handle cases like "RJ453,00 3,10 9,30")
                # More specific pattern to separate description from numbers
                numbers_pattern = r'^(.+?[A-Z]+\d*)\s*(\d+[.,]\d+)\s+(\d+[.,]\d+)\s+(\d+[.,]\d+)$'
                numbers_match = re.match(numbers_pattern, rest_of_line)
                
                if numbers_match:
                    # Single line format: "5020034022 UBIQUITI UNIFI POE INJECTOR 802.3BT 60W 1,00 24,90 24,90"
                    description = numbers_match.group(1).strip()
                    quantity_str = numbers_match.group(2).replace(',', '.')
                    unit_price_str = numbers_match.group(3).replace(',', '.')
                    total_amount_str = numbers_match.group(4).replace(',', '.')
                    
                    quantity = float(quantity_str)
                    unit_price = float(unit_price_str)
                    total_amount = float(total_amount_str)
                    
                    full_description = f"{description} (Art: {artikel_nummer})"
                    
                    dustin_items.append({
                        'description': full_description,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_amount': total_amount
                    })
                    
                    self.logger.debug(f"Extracted Dustin line item: {full_description} - {quantity}x €{unit_price:.2f} = €{total_amount:.2f}")
                
                else:
                    # Multi-line format: description continues on next line
                    # "5010967780 PROKORD TP-CABLE UTP CAT.6 UNSHIELDED LSZH RJ453,00 3,10 9,30"
                    # "3M GREY"
                    description_parts = [rest_of_line]
                    
                    # Look for continuation lines and numbers
                    for j in range(i+1, min(i+3, len(lines))):
                        next_line = lines[j].strip()
                        
                        # Check if this line has the numbers at the end
                        numbers_pattern = r'^(.+?)\s+(\d+[.,]\d+)\s+(\d+[.,]\d+)\s+(\d+[.,]\d+)$'
                        numbers_match = re.match(numbers_pattern, next_line)
                        
                        if numbers_match:
                            # Found the line with numbers
                            description_parts.append(numbers_match.group(1).strip())
                            
                            quantity_str = numbers_match.group(2).replace(',', '.')
                            unit_price_str = numbers_match.group(3).replace(',', '.')
                            total_amount_str = numbers_match.group(4).replace(',', '.')
                            
                            quantity = float(quantity_str)
                            unit_price = float(unit_price_str)
                            total_amount = float(total_amount_str)
                            
                            full_description = f"{' '.join(description_parts)} (Art: {artikel_nummer})"
                            
                            dustin_items.append({
                                'description': full_description,
                                'quantity': quantity,
                                'unit_price': unit_price,
                                'total_amount': total_amount
                            })
                            
                            self.logger.debug(f"Extracted Dustin multi-line item: {full_description} - {quantity}x €{unit_price:.2f} = €{total_amount:.2f}")
                            break
                        
                        # Check if this is just a description continuation (no numbers)
                        elif next_line and not re.match(r'^\d', next_line) and 'Vracht' not in next_line:
                            description_parts.append(next_line)
            
            # Also handle simple lines like "Vracht 1,00 4,99 4,99"
            elif line.startswith('Vracht'):
                vracht_pattern = r'^(Vracht)\s+(\d+[.,]\d+)\s+(\d+[.,]\d+)\s+(\d+[.,]\d+)$'
                match = re.match(vracht_pattern, line)
                
                if match:
                    description = match.group(1)
                    quantity_str = match.group(2).replace(',', '.')
                    unit_price_str = match.group(3).replace(',', '.')
                    total_amount_str = match.group(4).replace(',', '.')
                    
                    quantity = float(quantity_str)
                    unit_price = float(unit_price_str)
                    total_amount = float(total_amount_str)
                    
                    dustin_items.append({
                        'description': description,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total_amount': total_amount
                    })
                    
                    self.logger.debug(f"Extracted Dustin vracht: {description} - {quantity}x €{unit_price:.2f} = €{total_amount:.2f}")
        
        return dustin_items
    
    def _extract_dectdirect_line_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract DectDirect-specific line items from structured format."""
        
        dectdirect_items = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for DectDirect line items with format:
            # "1x Ubiquiti UniFi G4 Doorbell Pro € 302,00 € 302,00"
            # "Artikelcode: UVC-G4-DOORBELL-PRO BTW: 21% € 249,59 excl. BTW € 249,59 excl. BTW"
            dectdirect_pattern = r'^(\d+)x\s+(.+?)\s+€\s*(\d+[.,]\d{2})\s+€\s*(\d+[.,]\d{2})$'
            match = re.match(dectdirect_pattern, line)
            
            if match:
                quantity_str = match.group(1)
                description = match.group(2).strip()
                total_amount_str = match.group(4).replace(',', '.')
                
                quantity = float(quantity_str)
                total_amount = float(total_amount_str)
                
                # Look for the next line with excl. BTW price
                unit_price = total_amount / quantity  # fallback to inclusive price
                
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Look for "BTW: 21% € 249,59 excl. BTW € 249,59 excl. BTW"
                    excl_pattern = r'BTW:\s*\d+%\s+€\s*(\d+[.,]\d{2})\s+excl\.\s+BTW'
                    excl_match = re.search(excl_pattern, next_line)
                    if excl_match:
                        unit_price_str = excl_match.group(1).replace(',', '.')
                        unit_price = float(unit_price_str)
                
                dectdirect_items.append({
                    'description': description,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_amount': unit_price * quantity
                })
                
                self.logger.debug(f"Extracted DectDirect line item: {description} - {quantity}x €{unit_price:.2f} = €{unit_price * quantity:.2f}")
        
        return dectdirect_items
    
    def _extract_opslagruimte_line_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract Opslagruimte-specific line items from structured format."""
        
        opslagruimte_items = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for Opslagruimte line items with format:
            # "1 Huur opslagruimte 26, van de 25e tot de 25e deze maand € 45,00 0%"
            # Aantal Omschrijving Totaal Btw
            opslagruimte_pattern = r'^(\d+)\s+(.+?)\s+€\s*(\d+[.,]\d{2})\s+(\d+)%$'
            match = re.match(opslagruimte_pattern, line)
            
            if match:
                quantity_str = match.group(1)
                description = match.group(2).strip()
                total_amount_str = match.group(3).replace(',', '.')
                vat_percentage_str = match.group(4)
                
                quantity = float(quantity_str)
                total_amount = float(total_amount_str)
                vat_percentage = float(vat_percentage_str)
                
                # Unit price = total amount / quantity
                unit_price = total_amount / quantity if quantity > 0 else total_amount
                
                opslagruimte_items.append({
                    'description': description,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_amount': total_amount,
                    'vat_rate': vat_percentage
                })
                
                self.logger.debug(f"Extracted Opslagruimte line item: {description} - {quantity}x €{unit_price:.2f} = €{total_amount:.2f} ({vat_percentage}% BTW)")
        
        return opslagruimte_items
    
    def _extract_123accu_line_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract 123accu-specific line items from structured format."""
        
        accu_items = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for 123accu line items with format:
            # "1 ABS00006 Basis gereedschapset voor telefoon, tablet of laptop, 12-delig 21% € 4,95 € 4,95"
            # Aantal Artikelnummer Omschrijving btw Prijs Totaal
            accu_pattern = r'^(\d+)\s+([A-Z0-9]+)\s+(.+?)\s+(\d+)%\s+€\s*(\d+[.,]\d{2})\s+€\s*(\d+[.,]\d{2})$'
            match = re.match(accu_pattern, line)
            
            if match:
                quantity_str = match.group(1)
                artikel_nummer = match.group(2)
                description = match.group(3).strip()
                vat_percentage_str = match.group(4)
                unit_price_str = match.group(5).replace(',', '.')
                total_amount_str = match.group(6).replace(',', '.')
                
                quantity = float(quantity_str)
                vat_percentage = float(vat_percentage_str)
                unit_price_incl_vat = float(unit_price_str)
                total_amount_incl_vat = float(total_amount_str)
                
                # Calculate VAT-exclusive prices (for UBL XML)
                vat_multiplier = 1 + (vat_percentage / 100)
                unit_price = round(unit_price_incl_vat / vat_multiplier, 2)
                total_amount = round(total_amount_incl_vat / vat_multiplier, 2)
                
                # Add article number to description
                full_description = f"{description} (Art: {artikel_nummer})"
                
                accu_items.append({
                    'description': full_description,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_amount': total_amount,
                    'vat_rate': vat_percentage
                })
                
                self.logger.debug(f"Extracted 123accu line item: {full_description} - {quantity}x €{unit_price:.2f} = €{total_amount:.2f} ({vat_percentage}% BTW)")
        
        return accu_items
    
    def _extract_weservit_line_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract WeServit-specific line items from their unique format."""
        
        weservit_items = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for WeServit service descriptions (e.g., "Resources - Flexible Cloud 2017")
            if 'resources' in line.lower() or 'cloud' in line.lower():
                # Capture the main service description with date range
                description = line
                
                # Look for the pricing line (e.g., "Ja €15.00 EUR 1 €15.00 EUR")
                for j in range(i+1, min(i+10, len(lines))):
                    price_line = lines[j].strip()
                    
                    # Pattern: "Ja €15.00 EUR 1 €15.00 EUR"
                    # Format: BTW €PRICE CURRENCY QUANTITY €TOTAL
                    price_pattern = r'(?:Ja|Nee)\s+€(\d+[.,]\d{2})\s+EUR\s+(\d+)\s+€(\d+[.,]\d{2})\s+EUR'
                    match = re.search(price_pattern, price_line)
                    
                    if match:
                        unit_price_str = match.group(1).replace(',', '.')
                        quantity_str = match.group(2)
                        total_amount_str = match.group(3).replace(',', '.')
                        
                        unit_price = float(unit_price_str)
                        quantity = float(quantity_str)
                        total_amount = float(total_amount_str)
                        
                        # Collect additional details (CPUs, RAM, etc.)
                        details = []
                        for k in range(i+1, j):
                            detail_line = lines[k].strip()
                            if detail_line.startswith('+'):
                                details.append(detail_line)
                        
                        # Create full description with details
                        if details:
                            full_description = f"{description} - {', '.join(details)}"
                        else:
                            full_description = description
                        
                        weservit_items.append({
                            'description': full_description,
                            'quantity': quantity,
                            'unit_price': unit_price,
                            'total_amount': total_amount
                        })
                        
                        self.logger.debug(f"Extracted WeServit line item: {full_description} - {quantity}x €{unit_price:.2f} = €{total_amount:.2f}")
                        
                        i = j  # Skip processed lines
                        break
            
            i += 1
        
        return weservit_items
    
    def _extract_coolblue_line_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract Coolblue-specific line items with their structured format.
        
        Coolblue format: Product Description Quantity € Unit_Price VAT% € Total_Price
        Example: Apple iPhone 15 Pro Max 256GB Black Titanium 1 € 1.279,00 21% € 1.279,00
        """
        
        coolblue_items = []
        
        # Pattern for Coolblue line items
        pattern = r'^(.+?)\s+(\d+)\s+€\s*([\d\.]+,\d{2})\s+(\d+)%\s+€\s*([\d\.]+,\d{2})$'
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or 'Artikel' in line or 'Aantal' in line:
                continue
                
            # Skip summary lines
            if any(keyword in line for keyword in ['Exclusief BTW', 'BTW 21%', 'Totaal', 'Subtotaal', 'IMEI', 'Pagina']):
                continue
            
            match = re.match(pattern, line)
            if match:
                description = match.group(1).strip()
                quantity = int(match.group(2))
                unit_price_str = match.group(3)
                vat_percentage = int(match.group(4))
                total_price_str = match.group(5)
                
                # Parse amounts
                unit_price = self._parse_numeric_value(unit_price_str, remove_currency=True)
                total_price = self._parse_numeric_value(total_price_str, remove_currency=True)
                
                if unit_price is None or total_price is None:
                    continue
                
                # Calculate VAT-exclusive unit price for UBL
                unit_price_excl_vat = unit_price / (1 + vat_percentage / 100)
                total_price_excl_vat = total_price / (1 + vat_percentage / 100)
                
                coolblue_items.append({
                    'description': description,
                    'quantity': quantity,
                    'unit_price': unit_price_excl_vat,  # UBL requires VAT-exclusive prices
                    'total_amount': total_price_excl_vat,
                    'vat_percentage': vat_percentage,
                    'unit_price_incl_vat': unit_price,  # Store original price for reference
                    'total_amount_incl_vat': total_price
                })
                
                self.logger.debug(f"Extracted Coolblue line item: {description} - {quantity}x €{unit_price:.2f} (incl. VAT) = €{total_price:.2f}")
        
        return coolblue_items