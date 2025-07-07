"""Main UBL exporter module."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from ..extractors.pdf_extractor import ExtractedInvoiceData
from .ubl_models import UBLInvoice, UBLSupplier, UBLCustomer, UBLAddress, UBLTaxCategory
from .xml_generator import XMLGenerator

logger = logging.getLogger(__name__)


class UBLExporter:
    """Main UBL exporter class that converts extracted invoice data to UBL XML."""
    
    def __init__(self, 
                 default_currency: str = "EUR",
                 default_country: str = "NL",
                 default_vat_rate: Decimal = Decimal("21.00")):
        """Initialize UBL exporter.
        
        Args:
            default_currency: Default currency code
            default_country: Default country code
            default_vat_rate: Default VAT rate percentage
        """
        self.default_currency = default_currency
        self.default_country = default_country
        self.default_vat_rate = default_vat_rate
        self.xml_generator = XMLGenerator()
        self.logger = logging.getLogger(__name__)
    
    def export_to_ubl(self, 
                     extracted_data: ExtractedInvoiceData,
                     output_path: Optional[Path] = None,
                     template_config: Optional[Dict[str, Any]] = None) -> str:
        """Export extracted invoice data to UBL XML format.
        
        Args:
            extracted_data: Extracted invoice data
            output_path: Optional output file path
            template_config: Optional template configuration for field mapping
            
        Returns:
            UBL XML string
        """
        self.logger.info("Converting extracted data to UBL format")
        
        # Create UBL invoice
        ubl_invoice = self._create_ubl_invoice(extracted_data, template_config)
        
        # Generate XML
        xml_content = self.xml_generator.generate_xml(ubl_invoice)
        
        # Save to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            self.logger.info(f"UBL XML saved to {output_path}")
        
        return xml_content
    
    def _create_ubl_invoice(self, 
                           data: ExtractedInvoiceData,
                           template_config: Optional[Dict[str, Any]] = None) -> UBLInvoice:
        """Create UBL invoice from extracted data."""
        
        # Create base invoice
        issue_date = data.invoice_date or datetime.now()
        
        # Convert string date to datetime if needed
        if isinstance(issue_date, str):
            try:
                # Handle Dutch month names first
                dutch_months = {
                    'januari': 'January', 'februari': 'February', 'maart': 'March',
                    'april': 'April', 'mei': 'May', 'juni': 'June',
                    'juli': 'July', 'augustus': 'August', 'september': 'September',
                    'oktober': 'October', 'november': 'November', 'december': 'December'
                }
                
                # Replace Dutch month names with English for parsing
                date_str_en = issue_date
                for dutch, english in dutch_months.items():
                    date_str_en = date_str_en.replace(dutch, english)
                
                # Try common date formats including Dutch format
                for fmt in ['%d %B %Y', '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                    try:
                        issue_date = datetime.strptime(date_str_en, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # If no format works, use current date
                    issue_date = datetime.now()
            except:
                issue_date = datetime.now()
        
        due_date = data.due_date
        if due_date and isinstance(due_date, str):
            try:
                # Handle Dutch month names
                dutch_months = {
                    'januari': 'January', 'februari': 'February', 'maart': 'March',
                    'april': 'April', 'mei': 'May', 'juni': 'June',
                    'juli': 'July', 'augustus': 'August', 'september': 'September',
                    'oktober': 'October', 'november': 'November', 'december': 'December'
                }
                
                # Replace Dutch month names with English for parsing
                date_str_en = due_date
                for dutch, english in dutch_months.items():
                    date_str_en = date_str_en.replace(dutch, english)
                
                for fmt in ['%d %B %Y', '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                    try:
                        due_date = datetime.strptime(date_str_en, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    due_date = None
            except:
                due_date = None
        
        if not due_date:
            due_date = issue_date.replace(day=28) if issue_date.day < 28 else issue_date
        
        invoice = UBLInvoice(
            invoice_id=data.invoice_number or "UNKNOWN",
            issue_date=issue_date,
            due_date=due_date,
            document_currency_code=data.currency or self.default_currency,
            note=f"Generated from PDF extraction using {data.extraction_method}"
        )
        
        # Set supplier information (always required for UBL)
        supplier_name = data.supplier_name or "Unknown Supplier"
        invoice.set_supplier(
            name=supplier_name,
            address=data.supplier_address or "Unknown Address",
            vat_number=data.supplier_vat_number,
            iban=data.supplier_iban
        )
        
        # Set customer information (always required for UBL)
        customer_name = data.customer_name or "Customer"
        invoice.set_customer(
            name=customer_name,
            address=data.customer_address or "Customer Address",
            vat_number=data.customer_vat_number
        )
        
        # Add payment means
        if data.supplier_iban:
            invoice.add_payment_means(
                iban=data.supplier_iban,
                due_date=data.due_date
            )
        
        # Add line items
        self._add_line_items(invoice, data, template_config)
        
        # If no line items but we have total amounts, create a summary line
        if not invoice.invoice_lines and data.total_amount:
            self._add_summary_line_item(invoice, data)
        
        # Calculate totals
        invoice.calculate_totals()
        
        # Validate and adjust totals if needed
        self._validate_totals(invoice, data)
        
        return invoice
    
    def _add_line_items(self, 
                       invoice: UBLInvoice,
                       data: ExtractedInvoiceData,
                       template_config: Optional[Dict[str, Any]] = None):
        """Add line items to UBL invoice."""
        
        if not data.line_items:
            return
        
        for item_data in data.line_items:
            description = item_data.get('description', 'Unknown item')
            quantity = Decimal(str(item_data.get('quantity', 1)))
            unit_price = Decimal(str(item_data.get('unit_price', 0)))
            total_amount = Decimal(str(item_data.get('total_amount', 0)))
            
            # Calculate unit price if not provided but total is available
            if unit_price == 0 and total_amount > 0 and quantity > 0:
                unit_price = total_amount / quantity
            
            # Determine VAT rate
            vat_rate = self._determine_vat_rate(item_data, template_config)
            
            # Add line item
            invoice.add_line_item(
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                vat_rate=vat_rate,
                unit_code="EA"  # Each
            )
    
    def _add_summary_line_item(self, invoice: UBLInvoice, data: ExtractedInvoiceData):
        """Add a summary line item when no detailed items are available."""
        
        description = "Invoice total"
        
        # Calculate net amount
        net_amount = data.net_amount or data.total_amount
        if data.vat_amount and data.total_amount:
            net_amount = data.total_amount - data.vat_amount
        
        if not net_amount:
            net_amount = data.total_amount or Decimal('0.00')
        
        # Determine VAT rate
        vat_rate = self.default_vat_rate
        if data.vat_amount and net_amount and net_amount > 0:
            calculated_rate = (data.vat_amount / net_amount) * 100
            vat_rate = Decimal(str(round(calculated_rate, 2)))
        
        # Add summary line item
        invoice.add_line_item(
            description=description,
            quantity=Decimal('1.00'),
            unit_price=Decimal(str(net_amount)),
            vat_rate=vat_rate,
            unit_code="EA"
        )
    
    def _determine_vat_rate(self, 
                           item_data: Dict[str, Any],
                           template_config: Optional[Dict[str, Any]] = None) -> Decimal:
        """Determine VAT rate for line item."""
        
        # Check if VAT rate is provided in item data
        if 'vat_rate' in item_data and item_data['vat_rate'] is not None:
            return Decimal(str(item_data['vat_rate']))
        
        # Check template configuration
        if template_config and 'default_vat_rate' in template_config:
            return Decimal(str(template_config['default_vat_rate']))
        
        # Use default VAT rate
        return self.default_vat_rate
    
    def _validate_totals(self, invoice: UBLInvoice, data: ExtractedInvoiceData):
        """Validate and adjust totals if needed."""
        
        if not invoice.legal_monetary_total:
            return
        
        # Check if calculated totals match extracted totals
        calculated_total = invoice.legal_monetary_total.payable_amount
        extracted_total = data.total_amount
        
        if extracted_total and calculated_total:
            difference = abs(calculated_total - Decimal(str(extracted_total)))
            
            # If difference is significant, log warning
            if difference > Decimal('0.01'):
                self.logger.warning(
                    f"Total amount mismatch: calculated={calculated_total}, "
                    f"extracted={extracted_total}, difference={difference}"
                )
                
                # Optionally adjust if the difference is small
                if difference <= Decimal('1.00'):
                    self.logger.info("Adjusting calculated total to match extracted total")
                    invoice.legal_monetary_total.payable_amount = Decimal(str(extracted_total))
                    invoice.legal_monetary_total.tax_inclusive_amount = Decimal(str(extracted_total))
    
    def create_test_invoice(self) -> UBLInvoice:
        """Create a test UBL invoice for validation purposes."""
        
        invoice = UBLInvoice(
            invoice_id="TEST-2024-001",
            issue_date=datetime.now(),
            due_date=datetime.now().replace(day=28) if datetime.now().day < 28 else datetime.now(),
            document_currency_code="EUR",
            note="Test invoice generated by PDF2UBL"
        )
        
        # Set supplier
        invoice.set_supplier(
            name="Test Supplier B.V.",
            address="Teststraat 123\n1234 AB Amsterdam",
            vat_number="NL123456789B01",
            iban="NL91ABNA0417164300",
            contact_email="info@testsupplier.nl"
        )
        
        # Set customer
        invoice.set_customer(
            name="Test Customer B.V.",
            address="Klantlaan 456\n5678 CD Rotterdam",
            vat_number="NL987654321B01"
        )
        
        # Add payment means
        invoice.add_payment_means(
            iban="NL91ABNA0417164300",
            account_name="Test Supplier B.V.",
            due_date=invoice.due_date
        )
        
        # Add line items
        invoice.add_line_item(
            description="Test Product A",
            quantity=Decimal('2.00'),
            unit_price=Decimal('50.00'),
            vat_rate=Decimal('21.00')
        )
        
        invoice.add_line_item(
            description="Test Service B",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            vat_rate=Decimal('21.00')
        )
        
        # Calculate totals
        invoice.calculate_totals()
        
        return invoice
    
    def validate_ubl_xml(self, xml_content: str) -> bool:
        """Validate UBL XML content."""
        return self.xml_generator.validate_xml(xml_content)
    
    def export_test_invoice(self, output_path: Optional[Path] = None) -> str:
        """Export a test invoice for validation."""
        
        test_invoice = self.create_test_invoice()
        xml_content = self.xml_generator.generate_xml(test_invoice)
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            self.logger.info(f"Test UBL XML saved to {output_path}")
        
        return xml_content