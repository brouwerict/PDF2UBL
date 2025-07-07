"""UBL data models for invoice structure."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


@dataclass
class UBLAddress:
    """UBL Address structure."""
    street_name: Optional[str] = None
    building_number: Optional[str] = None
    postal_zone: Optional[str] = None  # Postal code
    city_name: Optional[str] = None
    country_code: str = "NL"
    address_lines: List[str] = field(default_factory=list)


@dataclass
class UBLParty:
    """Base UBL Party structure."""
    party_name: Optional[str] = None
    registration_name: Optional[str] = None
    company_id: Optional[str] = None  # KvK number
    address: Optional[UBLAddress] = None
    
    # Tax scheme (VAT)
    tax_scheme_id: Optional[str] = None  # VAT number
    tax_scheme_name: str = "BTW"
    
    # Contact information
    contact_name: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None


@dataclass
class UBLSupplier(UBLParty):
    """UBL Supplier (AccountingSupplierParty)."""
    pass


@dataclass
class UBLCustomer(UBLParty):
    """UBL Customer (AccountingCustomerParty)."""
    pass


@dataclass
class UBLTaxCategory:
    """UBL Tax Category structure."""
    tax_category_id: str = "S"  # Standard rate
    tax_category_name: str = "Standard rate"
    percent: Optional[Decimal] = None
    tax_scheme_id: str = "VAT"
    tax_scheme_name: str = "VAT"


@dataclass
class UBLTaxSubtotal:
    """UBL Tax Subtotal structure."""
    taxable_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    currency_code: str = "EUR"
    tax_category: Optional[UBLTaxCategory] = None


@dataclass
class UBLTaxTotal:
    """UBL Tax Total structure."""
    tax_amount: Decimal = Decimal('0.00')
    currency_code: str = "EUR"
    tax_subtotals: List[UBLTaxSubtotal] = field(default_factory=list)


@dataclass
class UBLPrice:
    """UBL Price structure."""
    price_amount: Decimal = Decimal('0.00')
    currency_code: str = "EUR"
    base_quantity: Decimal = Decimal('1.00')
    unit_code: str = "EA"  # Each


@dataclass
class UBLLineItem:
    """UBL Invoice Line structure."""
    line_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    invoiced_quantity: Decimal = Decimal('1.00')
    line_extension_amount: Decimal = Decimal('0.00')
    currency_code: str = "EUR"
    unit_code: str = "EA"  # Each
    
    # Item description
    item_name: Optional[str] = None
    item_description: Optional[str] = None
    item_classification_code: Optional[str] = None
    
    # Pricing
    price: Optional[UBLPrice] = None
    
    # Tax information
    tax_category: Optional[UBLTaxCategory] = None
    
    # Additional fields
    accounting_cost: Optional[str] = None
    note: Optional[str] = None


@dataclass
class UBLLegalMonetaryTotal:
    """UBL Legal Monetary Total structure."""
    line_extension_amount: Decimal = Decimal('0.00')
    tax_exclusive_amount: Decimal = Decimal('0.00')
    tax_inclusive_amount: Decimal = Decimal('0.00')
    allowance_total_amount: Decimal = Decimal('0.00')
    charge_total_amount: Decimal = Decimal('0.00')
    prepaid_amount: Decimal = Decimal('0.00')
    payable_amount: Decimal = Decimal('0.00')
    currency_code: str = "EUR"


@dataclass
class UBLPaymentMeans:
    """UBL Payment Means structure."""
    payment_means_code: str = "31"  # Bank transfer
    payment_due_date: Optional[datetime] = None
    payment_channel_code: Optional[str] = None
    instruction_id: Optional[str] = None
    
    # Bank account information
    payee_financial_account_id: Optional[str] = None  # IBAN
    payee_financial_account_name: Optional[str] = None
    financial_institution_id: Optional[str] = None  # BIC
    financial_institution_name: Optional[str] = None


@dataclass
class UBLInvoice:
    """Main UBL Invoice structure."""
    
    # Document identification
    invoice_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    invoice_type_code: str = "380"  # Commercial invoice
    note: Optional[str] = None
    document_currency_code: str = "EUR"
    
    # Parties
    supplier: Optional[UBLSupplier] = None
    customer: Optional[UBLCustomer] = None
    
    # Payment information
    payment_means: List[UBLPaymentMeans] = field(default_factory=list)
    
    # Tax information
    tax_total: List[UBLTaxTotal] = field(default_factory=list)
    
    # Monetary totals
    legal_monetary_total: Optional[UBLLegalMonetaryTotal] = None
    
    # Line items
    invoice_lines: List[UBLLineItem] = field(default_factory=list)
    
    # Additional fields
    order_reference: Optional[str] = None
    contract_reference: Optional[str] = None
    accounting_cost: Optional[str] = None
    
    # Customization and profile
    customization_id: str = "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:international:aunz:3.0"
    profile_id: str = "urn:fdc:peppol.eu:2017:poacc:billing:international:aunz:3.0"
    
    def calculate_totals(self):
        """Calculate all totals based on line items."""
        if not self.invoice_lines:
            return
        
        # Calculate line extension amount
        line_extension_amount = sum(line.line_extension_amount for line in self.invoice_lines)
        
        # Calculate tax amounts by category
        tax_categories = {}
        for line in self.invoice_lines:
            if line.tax_category:
                category_id = line.tax_category.tax_category_id
                if category_id not in tax_categories:
                    tax_categories[category_id] = {
                        'taxable_amount': Decimal('0.00'),
                        'tax_amount': Decimal('0.00'),
                        'tax_category': line.tax_category
                    }
                
                tax_categories[category_id]['taxable_amount'] += line.line_extension_amount
                
                if line.tax_category.percent:
                    tax_amount = line.line_extension_amount * (line.tax_category.percent / 100)
                    tax_categories[category_id]['tax_amount'] += tax_amount
        
        # Create tax subtotals
        tax_subtotals = []
        total_tax_amount = Decimal('0.00')
        
        for category_data in tax_categories.values():
            tax_subtotal = UBLTaxSubtotal(
                taxable_amount=category_data['taxable_amount'],
                tax_amount=category_data['tax_amount'],
                currency_code=self.document_currency_code,
                tax_category=category_data['tax_category']
            )
            tax_subtotals.append(tax_subtotal)
            total_tax_amount += category_data['tax_amount']
        
        # Create tax total
        if tax_subtotals:
            tax_total = UBLTaxTotal(
                tax_amount=total_tax_amount,
                currency_code=self.document_currency_code,
                tax_subtotals=tax_subtotals
            )
            self.tax_total = [tax_total]
        
        # Create legal monetary total
        self.legal_monetary_total = UBLLegalMonetaryTotal(
            line_extension_amount=line_extension_amount,
            tax_exclusive_amount=line_extension_amount,
            tax_inclusive_amount=line_extension_amount + total_tax_amount,
            payable_amount=line_extension_amount + total_tax_amount,
            currency_code=self.document_currency_code
        )
    
    def add_line_item(self, 
                     description: str,
                     quantity: Decimal = Decimal('1.00'),
                     unit_price: Decimal = Decimal('0.00'),
                     vat_rate: Optional[Decimal] = None,
                     unit_code: str = "EA") -> UBLLineItem:
        """Add a line item to the invoice."""
        
        line_extension_amount = quantity * unit_price
        
        # Create price
        price = UBLPrice(
            price_amount=unit_price,
            currency_code=self.document_currency_code,
            base_quantity=Decimal('1.00'),
            unit_code=unit_code
        )
        
        # Create tax category if VAT rate is provided
        tax_category = None
        if vat_rate is not None:
            tax_category = UBLTaxCategory(
                tax_category_id="S",
                tax_category_name="Standard rate",
                percent=vat_rate,
                tax_scheme_id="VAT",
                tax_scheme_name="VAT"
            )
        
        # Create line item
        line_item = UBLLineItem(
            line_id=str(len(self.invoice_lines) + 1),
            invoiced_quantity=quantity,
            line_extension_amount=line_extension_amount,
            currency_code=self.document_currency_code,
            unit_code=unit_code,
            item_name=description,
            item_description=description,
            price=price,
            tax_category=tax_category
        )
        
        self.invoice_lines.append(line_item)
        return line_item
    
    def set_supplier(self, name: str, address: str = None, vat_number: str = None, 
                    iban: str = None, contact_email: str = None) -> UBLSupplier:
        """Set supplier information."""
        
        supplier_address = None
        if address:
            # Parse address (basic implementation)
            address_lines = address.split('\n')
            supplier_address = UBLAddress(
                address_lines=address_lines,
                country_code="NL"
            )
        
        self.supplier = UBLSupplier(
            party_name=name,
            registration_name=name,
            address=supplier_address,
            tax_scheme_id=vat_number,
            email=contact_email
        )
        
        return self.supplier
    
    def set_customer(self, name: str, address: str = None, vat_number: str = None) -> UBLCustomer:
        """Set customer information."""
        
        customer_address = None
        if address:
            # Parse address (basic implementation)
            address_lines = address.split('\n')
            customer_address = UBLAddress(
                address_lines=address_lines,
                country_code="NL"
            )
        
        self.customer = UBLCustomer(
            party_name=name,
            registration_name=name,
            address=customer_address,
            tax_scheme_id=vat_number
        )
        
        return self.customer
    
    def add_payment_means(self, iban: str = None, bic: str = None, 
                         account_name: str = None, due_date: datetime = None) -> UBLPaymentMeans:
        """Add payment means information."""
        
        payment_means = UBLPaymentMeans(
            payment_means_code="31",  # Bank transfer
            payment_due_date=due_date,
            payee_financial_account_id=iban,
            payee_financial_account_name=account_name,
            financial_institution_id=bic
        )
        
        self.payment_means.append(payment_means)
        return payment_means