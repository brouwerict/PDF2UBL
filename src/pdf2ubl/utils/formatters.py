"""Formatting utilities for PDF2UBL."""

import re
from typing import Optional, Union
from datetime import datetime
from decimal import Decimal


def format_amount(amount: Union[str, float, Decimal], 
                 currency: str = "EUR",
                 decimal_places: int = 2,
                 use_thousands_separator: bool = True,
                 decimal_separator: str = ".",
                 thousands_separator: str = ",") -> str:
    """Format monetary amount for display.
    
    Args:
        amount: Amount to format
        currency: Currency code
        decimal_places: Number of decimal places
        use_thousands_separator: Whether to use thousands separator
        decimal_separator: Character for decimal separation
        thousands_separator: Character for thousands separation
        
    Returns:
        Formatted amount string
    """
    
    if amount is None:
        return ""
    
    try:
        # Convert to Decimal for precise formatting
        if isinstance(amount, str):
            # Clean input string
            clean_amount = amount.replace(',', '.')
            clean_amount = re.sub(r'[^\d.-]', '', clean_amount)
            decimal_amount = Decimal(clean_amount)
        else:
            decimal_amount = Decimal(str(amount))
        
        # Round to specified decimal places
        rounded_amount = decimal_amount.quantize(Decimal('0.' + '0' * decimal_places))
        
        # Convert to string
        amount_str = str(rounded_amount)
        
        # Split into integer and decimal parts
        if '.' in amount_str:
            integer_part, decimal_part = amount_str.split('.')
        else:
            integer_part = amount_str
            decimal_part = '0' * decimal_places
        
        # Add thousands separators
        if use_thousands_separator and len(integer_part) > 3:
            # Add separator every 3 digits from right
            integer_formatted = ""
            for i, digit in enumerate(reversed(integer_part)):
                if i > 0 and i % 3 == 0:
                    integer_formatted = thousands_separator + integer_formatted
                integer_formatted = digit + integer_formatted
        else:
            integer_formatted = integer_part
        
        # Combine parts
        if decimal_places > 0:
            formatted = integer_formatted + decimal_separator + decimal_part.ljust(decimal_places, '0')
        else:
            formatted = integer_formatted
        
        # Add currency
        if currency:
            if currency == "EUR":
                return f"€ {formatted}"
            elif currency == "USD":
                return f"$ {formatted}"
            elif currency == "GBP":
                return f"£ {formatted}"
            else:
                return f"{formatted} {currency}"
        
        return formatted
        
    except (ValueError, TypeError):
        return str(amount) if amount is not None else ""


def format_date(date: Union[str, datetime], 
               output_format: str = "%d-%m-%Y",
               input_formats: list = None) -> str:
    """Format date for display.
    
    Args:
        date: Date to format (string or datetime object)
        output_format: Output date format
        input_formats: List of possible input formats for string dates
        
    Returns:
        Formatted date string
    """
    
    if date is None:
        return ""
    
    if isinstance(date, datetime):
        return date.strftime(output_format)
    
    if isinstance(date, str):
        if not date.strip():
            return ""
        
        # Default input formats
        if input_formats is None:
            input_formats = [
                '%Y-%m-%d',
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%d-%m-%y',
                '%d/%m/%y',
                '%Y-%m-%d %H:%M:%S',
                '%d-%m-%Y %H:%M:%S'
            ]
        
        # Try to parse with each format
        for fmt in input_formats:
            try:
                parsed_date = datetime.strptime(date.strip(), fmt)
                return parsed_date.strftime(output_format)
            except ValueError:
                continue
        
        # If no format worked, return original string
        return date
    
    return str(date)


def format_vat_number(vat_number: str, country_code: str = "NL") -> str:
    """Format VAT number for display.
    
    Args:
        vat_number: VAT number to format
        country_code: Country code for formatting rules
        
    Returns:
        Formatted VAT number
    """
    
    if not vat_number:
        return ""
    
    # Remove spaces and convert to uppercase
    vat_clean = vat_number.replace(' ', '').upper()
    
    # Dutch VAT number formatting
    if country_code.upper() == "NL":
        if re.match(r'^NL\d{9}B\d{2}$', vat_clean):
            # Format as NL 123.456.789.B01
            return f"{vat_clean[:2]} {vat_clean[2:5]}.{vat_clean[5:8]}.{vat_clean[8:11]}.{vat_clean[11:]}"
    
    # Belgian VAT number formatting
    elif country_code.upper() == "BE":
        if re.match(r'^BE0\d{9}$', vat_clean):
            # Format as BE 0123.456.789
            return f"{vat_clean[:2]} {vat_clean[2:6]}.{vat_clean[6:9]}.{vat_clean[9:]}"
    
    # German VAT number formatting
    elif country_code.upper() == "DE":
        if re.match(r'^DE\d{9}$', vat_clean):
            # Format as DE 123456789
            return f"{vat_clean[:2]} {vat_clean[2:]}"
    
    # Default formatting (add space after country code)
    if len(vat_clean) >= 2:
        return f"{vat_clean[:2]} {vat_clean[2:]}"
    
    return vat_clean


def format_iban(iban: str, use_spaces: bool = True) -> str:
    """Format IBAN for display.
    
    Args:
        iban: IBAN to format
        use_spaces: Whether to add spaces for readability
        
    Returns:
        Formatted IBAN
    """
    
    if not iban:
        return ""
    
    # Remove spaces and convert to uppercase
    iban_clean = iban.replace(' ', '').upper()
    
    if not use_spaces:
        return iban_clean
    
    # Add spaces every 4 characters for readability
    formatted = ""
    for i, char in enumerate(iban_clean):
        if i > 0 and i % 4 == 0:
            formatted += " "
        formatted += char
    
    return formatted


def format_phone(phone: str, country_code: str = "NL") -> str:
    """Format phone number for display.
    
    Args:
        phone: Phone number to format
        country_code: Country code for formatting rules
        
    Returns:
        Formatted phone number
    """
    
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    phone_clean = re.sub(r'[^\d+]', '', phone)
    
    # Dutch phone number formatting
    if country_code.upper() == "NL":
        if phone_clean.startswith('+31'):
            # International format: +31 6 12345678
            number = phone_clean[3:]
            if len(number) == 9:
                return f"+31 {number[0]} {number[1:5]} {number[5:]}"
        elif phone_clean.startswith('06') and len(phone_clean) == 10:
            # Mobile: 06 12345678
            return f"{phone_clean[:2]} {phone_clean[2:6]} {phone_clean[6:]}"
        elif phone_clean.startswith('0') and len(phone_clean) == 10:
            # Landline: 020 1234567
            return f"{phone_clean[:3]} {phone_clean[3:6]} {phone_clean[6:]}"
    
    # Default formatting
    return phone


def format_percentage(value: Union[str, float, Decimal], decimal_places: int = 1) -> str:
    """Format percentage for display.
    
    Args:
        value: Percentage value to format
        decimal_places: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    
    if value is None:
        return ""
    
    try:
        if isinstance(value, str):
            # Remove % symbol if present
            clean_value = value.replace('%', '').strip()
            decimal_value = Decimal(clean_value)
        else:
            decimal_value = Decimal(str(value))
        
        # Round to specified decimal places
        rounded_value = decimal_value.quantize(Decimal('0.' + '0' * decimal_places))
        
        return f"{rounded_value}%"
        
    except (ValueError, TypeError):
        return str(value) if value is not None else ""


def format_invoice_number(invoice_number: str) -> str:
    """Format invoice number for display.
    
    Args:
        invoice_number: Invoice number to format
        
    Returns:
        Formatted invoice number
    """
    
    if not invoice_number:
        return ""
    
    # Remove extra whitespace
    formatted = invoice_number.strip()
    
    # Convert to uppercase if it contains letters
    if re.search(r'[a-zA-Z]', formatted):
        formatted = formatted.upper()
    
    return formatted


def format_company_name(company_name: str) -> str:
    """Format company name for display.
    
    Args:
        company_name: Company name to format
        
    Returns:
        Formatted company name
    """
    
    if not company_name:
        return ""
    
    # Remove extra whitespace
    formatted = ' '.join(company_name.split())
    
    # Capitalize first letter of each word, but preserve existing capitalization
    # for abbreviations like B.V., Ltd., etc.
    words = formatted.split()
    formatted_words = []
    
    for word in words:
        if word.upper() in ['B.V.', 'BV', 'LTD.', 'LTD', 'INC.', 'INC', 'GMBH', 'SARL', 'SAS']:
            formatted_words.append(word.upper())
        elif word.lower() in ['b.v.', 'ltd.', 'inc.']:
            formatted_words.append(word.upper())
        elif len(word) <= 3 and word.isupper():
            # Keep short uppercase words (likely abbreviations)
            formatted_words.append(word)
        else:
            formatted_words.append(word.capitalize())
    
    return ' '.join(formatted_words)


def format_address(address: str, separator: str = "\n") -> str:
    """Format address for display.
    
    Args:
        address: Address to format
        separator: Line separator
        
    Returns:
        Formatted address
    """
    
    if not address:
        return ""
    
    # Split into lines and clean each line
    lines = [line.strip() for line in address.split('\n')]
    lines = [line for line in lines if line]  # Remove empty lines
    
    # Join with specified separator
    return separator.join(lines)


def clean_text(text: str) -> str:
    """Clean text for processing.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    
    if not text:
        return ""
    
    # Remove extra whitespace
    cleaned = ' '.join(text.split())
    
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
    
    return cleaned.strip()