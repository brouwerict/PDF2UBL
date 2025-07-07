"""Amount formatting utilities for UBL XML."""

from decimal import Decimal, ROUND_HALF_UP


def format_amount_for_xml(amount, decimal_places=2):
    """Format amount for XML with specific decimal places.
    
    Args:
        amount: Amount to format (can be Decimal, float, or string)
        decimal_places: Number of decimal places (default: 2)
        
    Returns:
        String formatted amount with exact decimal places
    """
    if amount is None:
        return "0.00"
    
    # Convert to Decimal for precise calculation
    if isinstance(amount, str):
        decimal_amount = Decimal(amount.replace(',', '.'))
    else:
        decimal_amount = Decimal(str(amount))
    
    # Round to specified decimal places
    quantizer = Decimal('0.' + '0' * decimal_places)
    rounded_amount = decimal_amount.quantize(quantizer, rounding=ROUND_HALF_UP)
    
    # Format with exact decimal places
    return f"{rounded_amount:.{decimal_places}f}"


def format_percentage_for_xml(percentage):
    """Format percentage for XML (2 decimal places).
    
    Args:
        percentage: Percentage to format
        
    Returns:
        String formatted percentage
    """
    if percentage is None:
        return "0.00"
    
    decimal_percentage = Decimal(str(percentage))
    rounded_percentage = decimal_percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return f"{rounded_percentage:.2f}"


def format_quantity_for_xml(quantity):
    """Format quantity for XML (2 decimal places).
    
    Args:
        quantity: Quantity to format
        
    Returns:
        String formatted quantity
    """
    if quantity is None:
        return "1.00"
    
    decimal_quantity = Decimal(str(quantity))
    rounded_quantity = decimal_quantity.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return f"{rounded_quantity:.2f}"