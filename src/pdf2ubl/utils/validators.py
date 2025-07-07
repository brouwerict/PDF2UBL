"""Validation utilities for PDF2UBL."""

import re
from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
from lxml import etree


def validate_vat_number(vat_number: str, country_code: str = "NL") -> Tuple[bool, Optional[str]]:
    """Validate VAT number format.
    
    Args:
        vat_number: VAT number to validate
        country_code: Country code for validation rules
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not vat_number:
        return False, "VAT number is required"
    
    # Remove spaces and convert to uppercase
    vat_clean = vat_number.replace(' ', '').upper()
    
    # Dutch VAT number validation
    if country_code.upper() == "NL":
        if not re.match(r'^NL\d{9}B\d{2}$', vat_clean):
            return False, "Dutch VAT number must be in format NL123456789B01"
        
        # Extract numeric part for checksum validation
        numeric_part = vat_clean[2:11]
        
        # Calculate checksum (simplified - real validation is more complex)
        try:
            digits = [int(d) for d in numeric_part]
            checksum = sum(digits[i] * (9 - i) for i in range(8))
            
            if checksum % 11 < 2:
                expected_check = checksum % 11
            else:
                expected_check = 11 - (checksum % 11)
            
            actual_check = int(numeric_part[8])
            
            if actual_check != expected_check:
                return False, "Invalid VAT number checksum"
            
        except (ValueError, IndexError):
            return False, "Invalid VAT number format"
    
    # Belgian VAT number validation
    elif country_code.upper() == "BE":
        if not re.match(r'^BE0\d{9}$', vat_clean):
            return False, "Belgian VAT number must be in format BE0123456789"
    
    # German VAT number validation
    elif country_code.upper() == "DE":
        if not re.match(r'^DE\d{9}$', vat_clean):
            return False, "German VAT number must be in format DE123456789"
    
    # Generic EU VAT number validation
    else:
        if not re.match(r'^[A-Z]{2}[\dA-Z]+$', vat_clean):
            return False, "VAT number must start with two-letter country code"
    
    return True, None


def validate_iban(iban: str) -> Tuple[bool, Optional[str]]:
    """Validate IBAN format and checksum.
    
    Args:
        iban: IBAN to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not iban:
        return False, "IBAN is required"
    
    # Remove spaces and convert to uppercase
    iban_clean = iban.replace(' ', '').upper()
    
    # Check length (minimum 15, maximum 34 characters)
    if len(iban_clean) < 15 or len(iban_clean) > 34:
        return False, "IBAN length must be between 15 and 34 characters"
    
    # Check format (2 letters + 2 digits + alphanumeric)
    if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]+$', iban_clean):
        return False, "IBAN must start with 2 letters and 2 digits"
    
    # IBAN checksum validation (MOD-97)
    try:
        # Move first 4 characters to end
        rearranged = iban_clean[4:] + iban_clean[:4]
        
        # Replace letters with numbers (A=10, B=11, ..., Z=35)
        numeric_string = ''
        for char in rearranged:
            if char.isalpha():
                numeric_string += str(ord(char) - ord('A') + 10)
            else:
                numeric_string += char
        
        # Calculate MOD-97
        remainder = int(numeric_string) % 97
        
        if remainder != 1:
            return False, "Invalid IBAN checksum"
        
    except (ValueError, OverflowError):
        return False, "Invalid IBAN format"
    
    return True, None


def validate_amount(amount_str: str, min_value: float = 0.0, max_value: float = 1000000.0) -> Tuple[bool, Optional[str], Optional[Decimal]]:
    """Validate monetary amount.
    
    Args:
        amount_str: Amount string to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Tuple of (is_valid, error_message, parsed_amount)
    """
    
    if not amount_str:
        return False, "Amount is required", None
    
    try:
        # Clean amount string
        cleaned = amount_str.strip()
        
        # Remove currency symbols
        cleaned = re.sub(r'[€$£\s]', '', cleaned)
        
        # Handle European decimal format (comma as decimal separator)
        if ',' in cleaned and '.' in cleaned:
            # Format like "1.234,56"
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # Check if it's thousands separator or decimal separator
            comma_pos = cleaned.rfind(',')
            after_comma = cleaned[comma_pos + 1:]
            
            if len(after_comma) == 2 and after_comma.isdigit():
                # Decimal separator
                cleaned = cleaned.replace(',', '.')
            else:
                # Thousands separator
                cleaned = cleaned.replace(',', '')
        
        # Parse as decimal
        amount = Decimal(cleaned)
        
        # Validate range
        if amount < Decimal(str(min_value)):
            return False, f"Amount must be at least {min_value}", None
        
        if amount > Decimal(str(max_value)):
            return False, f"Amount must not exceed {max_value}", None
        
        return True, None, amount
        
    except (ValueError, TypeError):
        return False, "Invalid amount format", None


def validate_date(date_str: str, date_formats: List[str] = None) -> Tuple[bool, Optional[str], Optional[datetime]]:
    """Validate date string.
    
    Args:
        date_str: Date string to validate
        date_formats: List of allowed date formats
        
    Returns:
        Tuple of (is_valid, error_message, parsed_date)
    """
    
    if not date_str:
        return False, "Date is required", None
    
    if date_formats is None:
        date_formats = [
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%y',
            '%d/%m/%y',
            '%d %B %Y',
            '%d %b %Y'
        ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str.strip(), fmt)
            
            # Validate reasonable date range
            current_year = datetime.now().year
            if parsed_date.year < 1900 or parsed_date.year > current_year + 10:
                return False, f"Date year must be between 1900 and {current_year + 10}", None
            
            return True, None, parsed_date
            
        except ValueError:
            continue
    
    return False, f"Date format not recognized. Expected formats: {', '.join(date_formats)}", None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not email:
        return False, "Email is required"
    
    # Basic email validation regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, None


def validate_phone(phone: str, country_code: str = "NL") -> Tuple[bool, Optional[str]]:
    """Validate phone number format.
    
    Args:
        phone: Phone number to validate
        country_code: Country code for validation rules
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    if not phone:
        return False, "Phone number is required"
    
    # Remove common separators
    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Dutch phone number validation
    if country_code.upper() == "NL":
        # Dutch mobile: +31 6 xxxxxxxx or 06 xxxxxxxx
        # Dutch landline: +31 xx xxxxxxx or 0xx xxxxxxx
        if not re.match(r'^(\+31|0)[1-9]\d{8}$', phone_clean):
            return False, "Invalid Dutch phone number format"
    
    # Generic international format
    else:
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone_clean):
            return False, "Invalid phone number format"
    
    return True, None


def validate_ubl(xml_content: str) -> Tuple[bool, List[str]]:
    """Validate UBL XML content.
    
    Args:
        xml_content: UBL XML content to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    
    errors = []
    
    try:
        # Parse XML
        root = etree.fromstring(xml_content.encode('utf-8'))
        
        # Check root element
        if root.tag.split('}')[-1] != 'Invoice':
            errors.append("Root element must be 'Invoice'")
        
        # Check namespace
        expected_ns = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
        if root.nsmap.get(None) != expected_ns:
            errors.append(f"Invalid namespace. Expected: {expected_ns}")
        
        # Check required elements
        required_elements = [
            "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID",
            "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate",
            "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode"
        ]
        
        for element in required_elements:
            if root.find(element) is None:
                element_name = element.split('}')[-1]
                errors.append(f"Required element missing: {element_name}")
        
        # Check invoice ID format
        invoice_id_elem = root.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
        if invoice_id_elem is not None:
            invoice_id = invoice_id_elem.text
            if not invoice_id or len(invoice_id.strip()) == 0:
                errors.append("Invoice ID cannot be empty")
        
        # Check date format
        issue_date_elem = root.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate")
        if issue_date_elem is not None:
            date_text = issue_date_elem.text
            if date_text:
                try:
                    datetime.strptime(date_text, '%Y-%m-%d')
                except ValueError:
                    errors.append("IssueDate must be in YYYY-MM-DD format")
        
        # Check currency code
        currency_elem = root.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode")
        if currency_elem is not None:
            currency = currency_elem.text
            if currency and len(currency) != 3:
                errors.append("DocumentCurrencyCode must be 3 characters (ISO 4217)")
        
        # Check suppliers and customers
        supplier_party = root.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty")
        if supplier_party is None:
            errors.append("AccountingSupplierParty is required")
        
        customer_party = root.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty")
        if customer_party is None:
            errors.append("AccountingCustomerParty is required")
        
        # Check monetary totals
        monetary_total = root.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal")
        if monetary_total is None:
            errors.append("LegalMonetaryTotal is required")
        else:
            # Check required monetary amounts
            required_amounts = [
                "LineExtensionAmount",
                "TaxExclusiveAmount",
                "TaxInclusiveAmount",
                "PayableAmount"
            ]
            
            for amount_name in required_amounts:
                amount_elem = monetary_total.find(f"{{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}}{amount_name}")
                if amount_elem is None:
                    errors.append(f"LegalMonetaryTotal/{amount_name} is required")
                else:
                    # Validate amount format
                    amount_text = amount_elem.text
                    if amount_text:
                        try:
                            float(amount_text)
                        except ValueError:
                            errors.append(f"Invalid amount format in {amount_name}: {amount_text}")
        
        # Check invoice lines
        invoice_lines = root.findall("{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine")
        if not invoice_lines:
            errors.append("At least one InvoiceLine is required")
        else:
            for i, line in enumerate(invoice_lines, 1):
                line_id = line.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
                if line_id is None or not line_id.text:
                    errors.append(f"InvoiceLine {i}: ID is required")
                
                invoiced_qty = line.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoicedQuantity")
                if invoiced_qty is None:
                    errors.append(f"InvoiceLine {i}: InvoicedQuantity is required")
                
                line_ext_amount = line.find("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount")
                if line_ext_amount is None:
                    errors.append(f"InvoiceLine {i}: LineExtensionAmount is required")
        
        return len(errors) == 0, errors
        
    except etree.XMLSyntaxError as e:
        errors.append(f"XML syntax error: {str(e)}")
        return False, errors
    
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, errors


def validate_invoice_data(data: dict) -> Tuple[bool, List[str]]:
    """Validate extracted invoice data.
    
    Args:
        data: Dictionary with invoice data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    
    errors = []
    
    # Check required fields
    required_fields = ['invoice_number', 'invoice_date', 'total_amount']
    
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Required field missing: {field}")
    
    # Validate specific fields
    if 'invoice_number' in data and data['invoice_number']:
        invoice_number = str(data['invoice_number']).strip()
        if len(invoice_number) == 0:
            errors.append("Invoice number cannot be empty")
        elif len(invoice_number) > 50:
            errors.append("Invoice number too long (max 50 characters)")
    
    if 'invoice_date' in data and data['invoice_date']:
        if isinstance(data['invoice_date'], str):
            is_valid, error, _ = validate_date(data['invoice_date'])
            if not is_valid:
                errors.append(f"Invalid invoice date: {error}")
    
    if 'total_amount' in data and data['total_amount']:
        if isinstance(data['total_amount'], str):
            is_valid, error, _ = validate_amount(data['total_amount'])
            if not is_valid:
                errors.append(f"Invalid total amount: {error}")
    
    if 'supplier_vat_number' in data and data['supplier_vat_number']:
        is_valid, error = validate_vat_number(data['supplier_vat_number'])
        if not is_valid:
            errors.append(f"Invalid supplier VAT number: {error}")
    
    if 'supplier_iban' in data and data['supplier_iban']:
        is_valid, error = validate_iban(data['supplier_iban'])
        if not is_valid:
            errors.append(f"Invalid supplier IBAN: {error}")
    
    return len(errors) == 0, errors