"""Text extraction utilities for PDF processing."""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TextRegion:
    """Represents a text region with positioning information."""
    text: str
    x: float
    y: float
    width: float
    height: float
    font_size: float
    font_name: str = ""


class TextExtractor:
    """Advanced text extraction with pattern matching and positioning."""
    
    def __init__(self):
        self.date_patterns = [
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
            r'\b(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4})\b',
            r'\b(\d{1,2}\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+\d{2,4})\b',
        ]
        
        self.amount_patterns = [
            r'€\s*(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})\s*€',
            r'\b(\d+[.,]\d{2})\b',
        ]
        
        self.vat_patterns = [
            r'(?:BTW|VAT)[-\s]*(?:nr|nummer|number)?[:\s]*([A-Z]{2}\d{9}B\d{2})',
            r'([A-Z]{2}\d{9}B\d{2})',
        ]
        
        self.invoice_patterns = [
            r'(?:factuur|invoice)[-\s]*(?:nr|nummer|number)?[:\s#]*(\w+)',
            r'(?:nr|no)[:\s.]*(\w+)',
        ]
    
    def extract_dates(self, text: str) -> List[Tuple[str, datetime, float]]:
        """Extract dates with confidence scores.
        
        Returns:
            List of (original_text, parsed_date, confidence_score)
        """
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    confidence = self._calculate_date_confidence(date_str, pattern)
                    dates.append((date_str, parsed_date, confidence))
        
        return dates
    
    def extract_amounts(self, text: str) -> List[Tuple[str, float, float]]:
        """Extract monetary amounts with confidence scores.
        
        Returns:
            List of (original_text, amount, confidence_score)
        """
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1)
                amount = self._parse_amount(amount_str)
                if amount is not None:
                    confidence = self._calculate_amount_confidence(amount_str, pattern)
                    amounts.append((amount_str, amount, confidence))
        
        return amounts
    
    def extract_vat_numbers(self, text: str) -> List[Tuple[str, str, float]]:
        """Extract VAT numbers with confidence scores.
        
        Returns:
            List of (original_text, vat_number, confidence_score)
        """
        vat_numbers = []
        
        for pattern in self.vat_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                vat_str = match.group(1) if match.lastindex > 0 else match.group(0)
                if self._validate_vat_number(vat_str):
                    confidence = 0.9 if 'BTW' in match.group(0) or 'VAT' in match.group(0) else 0.7
                    vat_numbers.append((match.group(0), vat_str, confidence))
        
        return vat_numbers
    
    def extract_invoice_numbers(self, text: str) -> List[Tuple[str, str, float]]:
        """Extract invoice numbers with confidence scores.
        
        Returns:
            List of (original_text, invoice_number, confidence_score)
        """
        invoice_numbers = []
        
        for pattern in self.invoice_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                invoice_num = match.group(1)
                confidence = self._calculate_invoice_confidence(invoice_num, pattern)
                invoice_numbers.append((match.group(0), invoice_num, confidence))
        
        return invoice_numbers
    
    def extract_addresses(self, text: str) -> List[Tuple[str, float]]:
        """Extract addresses with confidence scores.
        
        Returns:
            List of (address, confidence_score)
        """
        addresses = []
        
        # Split text into lines and look for address patterns
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if self._looks_like_address(line):
                # Try to build a complete address
                address_lines = [line]
                
                # Look for postal code in next few lines
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if self._looks_like_postal_code(next_line):
                        address_lines.append(next_line)
                        break
                    elif len(next_line) > 0 and not self._looks_like_invoice_field(next_line):
                        address_lines.append(next_line)
                
                if len(address_lines) > 1:
                    full_address = '\n'.join(address_lines)
                    confidence = self._calculate_address_confidence(full_address)
                    addresses.append((full_address, confidence))
        
        return addresses
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object."""
        formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%d %B %Y', '%d %b %Y',
        ]
        
        # Handle Dutch month names
        dutch_months = {
            'januari': 'january', 'februari': 'february', 'maart': 'march',
            'april': 'april', 'mei': 'may', 'juni': 'june',
            'juli': 'july', 'augustus': 'august', 'september': 'september',
            'oktober': 'october', 'november': 'november', 'december': 'december'
        }
        
        date_str = date_str.lower()
        for dutch, english in dutch_months.items():
            date_str = date_str.replace(dutch, english)
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string into float."""
        try:
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[€$£¥\s]', '', amount_str.strip())
            
            # Handle different number formats
            if ',' in cleaned and '.' in cleaned:
                # Thousands and decimal separators present
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
        except ValueError:
            return None
    
    def _validate_vat_number(self, vat_str: str) -> bool:
        """Validate VAT number format."""
        # Basic validation for Dutch VAT numbers
        pattern = r'^[A-Z]{2}\d{9}B\d{2}$'
        return bool(re.match(pattern, vat_str))
    
    def _looks_like_address(self, line: str) -> bool:
        """Check if line looks like start of an address."""
        # Look for street names, house numbers
        if re.search(r'\d+[a-zA-Z]?\s', line):  # House number
            return True
        if re.search(r'(straat|laan|weg|plein|kade|gracht)', line, re.IGNORECASE):  # Dutch street types
            return True
        if re.search(r'(street|avenue|road|lane|drive)', line, re.IGNORECASE):  # English street types
            return True
        return False
    
    def _looks_like_postal_code(self, line: str) -> bool:
        """Check if line contains a postal code."""
        # Dutch postal code pattern
        if re.search(r'\d{4}\s*[A-Z]{2}', line):
            return True
        # International postal codes
        if re.search(r'\d{4,5}', line):
            return True
        return False
    
    def _looks_like_invoice_field(self, line: str) -> bool:
        """Check if line looks like an invoice field rather than address."""
        field_indicators = [
            'factuur', 'invoice', 'bedrag', 'amount', 'btw', 'vat',
            'datum', 'date', 'totaal', 'total', 'nummer', 'number'
        ]
        return any(indicator in line.lower() for indicator in field_indicators)
    
    def _calculate_date_confidence(self, date_str: str, pattern: str) -> float:
        """Calculate confidence score for date extraction."""
        confidence = 0.5
        
        # Higher confidence for more specific patterns
        if re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', date_str):
            confidence += 0.3
        
        # Lower confidence for 2-digit years
        if re.search(r'\d{2}$', date_str):
            confidence -= 0.1
        
        # Higher confidence for month names
        if any(month in date_str.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                                       'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _calculate_amount_confidence(self, amount_str: str, pattern: str) -> float:
        """Calculate confidence score for amount extraction."""
        confidence = 0.5
        
        # Higher confidence for currency symbols
        if '€' in pattern:
            confidence += 0.3
        
        # Higher confidence for decimal amounts
        if '.' in amount_str or ',' in amount_str:
            confidence += 0.2
        
        # Lower confidence for very small or very large amounts
        try:
            amount = float(amount_str.replace(',', '.'))
            if amount < 1 or amount > 100000:
                confidence -= 0.2
        except ValueError:
            pass
        
        return min(confidence, 1.0)
    
    def _calculate_invoice_confidence(self, invoice_num: str, pattern: str) -> float:
        """Calculate confidence score for invoice number extraction."""
        confidence = 0.5
        
        # Higher confidence for explicit invoice patterns
        if 'factuur' in pattern.lower() or 'invoice' in pattern.lower():
            confidence += 0.3
        
        # Higher confidence for alphanumeric patterns
        if re.search(r'[A-Z]', invoice_num) and re.search(r'\d', invoice_num):
            confidence += 0.2
        
        # Lower confidence for very short or very long numbers
        if len(invoice_num) < 3 or len(invoice_num) > 20:
            confidence -= 0.2
        
        return min(confidence, 1.0)
    
    def _calculate_address_confidence(self, address: str) -> float:
        """Calculate confidence score for address extraction."""
        confidence = 0.5
        
        # Higher confidence for multiple lines
        if '\n' in address:
            confidence += 0.2
        
        # Higher confidence for postal codes
        if re.search(r'\d{4}\s*[A-Z]{2}', address):
            confidence += 0.3
        
        # Higher confidence for street indicators
        street_indicators = ['straat', 'laan', 'weg', 'plein', 'street', 'avenue', 'road']
        if any(indicator in address.lower() for indicator in street_indicators):
            confidence += 0.2
        
        return min(confidence, 1.0)