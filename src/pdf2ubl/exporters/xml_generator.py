"""XML generation utilities for UBL documents."""

from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from lxml import etree
from .ubl_models import UBLInvoice, UBLAddress, UBLParty, UBLLineItem, UBLTaxTotal, UBLTaxSubtotal
from ..utils.amount_formatter import format_amount_for_xml, format_percentage_for_xml, format_quantity_for_xml


class XMLGenerator:
    """Generate UBL XML from UBL models."""
    
    def __init__(self):
        self.namespaces = {
            None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }
        
        self.schema_location = (
            "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 "
            "http://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd"
        )
    
    def generate_xml(self, invoice: UBLInvoice) -> str:
        """Generate UBL XML string from UBL invoice model."""
        
        # Create root element
        root = etree.Element("Invoice", nsmap=self.namespaces)
        root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", self.schema_location)
        
        # Add document-level information
        self._add_document_info(root, invoice)
        
        # Add parties
        self._add_parties(root, invoice)
        
        # Add payment means
        self._add_payment_means(root, invoice)
        
        # Add tax totals
        self._add_tax_totals(root, invoice)
        
        # Add legal monetary total
        self._add_legal_monetary_total(root, invoice)
        
        # Add invoice lines
        self._add_invoice_lines(root, invoice)
        
        # Generate XML string
        return etree.tostring(root, encoding='unicode', pretty_print=True)
    
    def _add_document_info(self, root: etree.Element, invoice: UBLInvoice):
        """Add document-level information to XML."""
        
        # CustomizationID
        customization_id = etree.SubElement(root, self._qname("cbc", "CustomizationID"))
        customization_id.text = invoice.customization_id
        
        # ProfileID
        profile_id = etree.SubElement(root, self._qname("cbc", "ProfileID"))
        profile_id.text = invoice.profile_id
        
        # ID
        id_elem = etree.SubElement(root, self._qname("cbc", "ID"))
        id_elem.text = invoice.invoice_id
        
        # IssueDate (required)
        issue_date = etree.SubElement(root, self._qname("cbc", "IssueDate"))
        if invoice.issue_date:
            issue_date.text = invoice.issue_date.strftime("%Y-%m-%d")
        else:
            issue_date.text = datetime.now().strftime("%Y-%m-%d")
        
        # DueDate (often required by accounting software)
        due_date = etree.SubElement(root, self._qname("cbc", "DueDate"))
        if invoice.due_date:
            due_date.text = invoice.due_date.strftime("%Y-%m-%d")
        else:
            # Default to 30 days from issue date
            default_due = (invoice.issue_date or datetime.now()).replace(day=28)
            due_date.text = default_due.strftime("%Y-%m-%d")
        
        # InvoiceTypeCode
        invoice_type_code = etree.SubElement(root, self._qname("cbc", "InvoiceTypeCode"))
        invoice_type_code.text = invoice.invoice_type_code
        
        # Note
        if invoice.note:
            note = etree.SubElement(root, self._qname("cbc", "Note"))
            note.text = invoice.note
        
        # DocumentCurrencyCode
        currency_code = etree.SubElement(root, self._qname("cbc", "DocumentCurrencyCode"))
        currency_code.text = invoice.document_currency_code
        
        # OrderReference
        if invoice.order_reference:
            order_ref = etree.SubElement(root, self._qname("cac", "OrderReference"))
            order_id = etree.SubElement(order_ref, self._qname("cbc", "ID"))
            order_id.text = invoice.order_reference
    
    def _add_parties(self, root: etree.Element, invoice: UBLInvoice):
        """Add supplier and customer parties to XML."""
        
        # AccountingSupplierParty
        if invoice.supplier:
            supplier_party = etree.SubElement(root, self._qname("cac", "AccountingSupplierParty"))
            self._add_party(supplier_party, invoice.supplier, "Supplier")
        
        # AccountingCustomerParty
        if invoice.customer:
            customer_party = etree.SubElement(root, self._qname("cac", "AccountingCustomerParty"))
            self._add_party(customer_party, invoice.customer, "Customer")
    
    def _add_party(self, parent: etree.Element, party: UBLParty, party_type: str):
        """Add party information to XML."""
        
        party_elem = etree.SubElement(parent, self._qname("cac", "Party"))
        
        # PartyName
        if party.party_name:
            party_name = etree.SubElement(party_elem, self._qname("cac", "PartyName"))
            name = etree.SubElement(party_name, self._qname("cbc", "Name"))
            name.text = party.party_name
        
        # PostalAddress
        if party.address:
            postal_address = etree.SubElement(party_elem, self._qname("cac", "PostalAddress"))
            self._add_address(postal_address, party.address)
        
        # PartyTaxScheme
        if party.tax_scheme_id:
            party_tax_scheme = etree.SubElement(party_elem, self._qname("cac", "PartyTaxScheme"))
            
            company_id = etree.SubElement(party_tax_scheme, self._qname("cbc", "CompanyID"))
            company_id.text = party.tax_scheme_id
            
            tax_scheme = etree.SubElement(party_tax_scheme, self._qname("cac", "TaxScheme"))
            tax_scheme_id = etree.SubElement(tax_scheme, self._qname("cbc", "ID"))
            tax_scheme_id.text = "VAT"
        
        # PartyLegalEntity
        if party.registration_name:
            party_legal_entity = etree.SubElement(party_elem, self._qname("cac", "PartyLegalEntity"))
            registration_name = etree.SubElement(party_legal_entity, self._qname("cbc", "RegistrationName"))
            registration_name.text = party.registration_name
            
            if party.company_id:
                company_legal_form = etree.SubElement(party_legal_entity, self._qname("cbc", "CompanyID"))
                company_legal_form.text = party.company_id
        
        # Contact
        if party.contact_name or party.telephone or party.email:
            contact = etree.SubElement(party_elem, self._qname("cac", "Contact"))
            
            if party.contact_name:
                contact_name = etree.SubElement(contact, self._qname("cbc", "Name"))
                contact_name.text = party.contact_name
            
            if party.telephone:
                telephone = etree.SubElement(contact, self._qname("cbc", "Telephone"))
                telephone.text = party.telephone
            
            if party.email:
                email = etree.SubElement(contact, self._qname("cbc", "ElectronicMail"))
                email.text = party.email
    
    def _add_address(self, parent: etree.Element, address: UBLAddress):
        """Add address information to XML."""
        
        if address.street_name:
            street_name = etree.SubElement(parent, self._qname("cbc", "StreetName"))
            street_name.text = address.street_name
        
        if address.building_number:
            building_number = etree.SubElement(parent, self._qname("cbc", "BuildingNumber"))
            building_number.text = address.building_number
        
        if address.city_name:
            city_name = etree.SubElement(parent, self._qname("cbc", "CityName"))
            city_name.text = address.city_name
        
        if address.postal_zone:
            postal_zone = etree.SubElement(parent, self._qname("cbc", "PostalZone"))
            postal_zone.text = address.postal_zone
        
        if address.country_code:
            country = etree.SubElement(parent, self._qname("cac", "Country"))
            country_code = etree.SubElement(country, self._qname("cbc", "IdentificationCode"))
            country_code.text = address.country_code
        
        # Add address lines
        for line in address.address_lines:
            if line.strip():
                address_line = etree.SubElement(parent, self._qname("cbc", "AddressLine"))
                line_elem = etree.SubElement(address_line, self._qname("cbc", "Line"))
                line_elem.text = line.strip()
    
    def _add_payment_means(self, root: etree.Element, invoice: UBLInvoice):
        """Add payment means to XML."""
        
        for payment_means in invoice.payment_means:
            payment_means_elem = etree.SubElement(root, self._qname("cac", "PaymentMeans"))
            
            # PaymentMeansCode
            payment_means_code = etree.SubElement(payment_means_elem, self._qname("cbc", "PaymentMeansCode"))
            payment_means_code.text = payment_means.payment_means_code
            
            # PaymentDueDate
            if payment_means.payment_due_date:
                payment_due_date = etree.SubElement(payment_means_elem, self._qname("cbc", "PaymentDueDate"))
                payment_due_date.text = payment_means.payment_due_date.strftime("%Y-%m-%d")
            
            # PayeeFinancialAccount
            if payment_means.payee_financial_account_id:
                payee_account = etree.SubElement(payment_means_elem, self._qname("cac", "PayeeFinancialAccount"))
                
                account_id = etree.SubElement(payee_account, self._qname("cbc", "ID"))
                account_id.text = payment_means.payee_financial_account_id
                
                if payment_means.payee_financial_account_name:
                    account_name = etree.SubElement(payee_account, self._qname("cbc", "Name"))
                    account_name.text = payment_means.payee_financial_account_name
                
                # FinancialInstitutionBranch
                if payment_means.financial_institution_id:
                    institution_branch = etree.SubElement(payee_account, self._qname("cac", "FinancialInstitutionBranch"))
                    institution_id = etree.SubElement(institution_branch, self._qname("cbc", "ID"))
                    institution_id.text = payment_means.financial_institution_id
                    
                    if payment_means.financial_institution_name:
                        institution_name = etree.SubElement(institution_branch, self._qname("cbc", "Name"))
                        institution_name.text = payment_means.financial_institution_name
    
    def _add_tax_totals(self, root: etree.Element, invoice: UBLInvoice):
        """Add tax totals to XML."""
        
        for tax_total in invoice.tax_total:
            tax_total_elem = etree.SubElement(root, self._qname("cac", "TaxTotal"))
            
            # TaxAmount
            tax_amount = etree.SubElement(tax_total_elem, self._qname("cbc", "TaxAmount"))
            tax_amount.text = format_amount_for_xml(tax_total.tax_amount)
            tax_amount.set("currencyID", tax_total.currency_code)
            
            # TaxSubtotals
            for tax_subtotal in tax_total.tax_subtotals:
                tax_subtotal_elem = etree.SubElement(tax_total_elem, self._qname("cac", "TaxSubtotal"))
                
                # TaxableAmount
                taxable_amount = etree.SubElement(tax_subtotal_elem, self._qname("cbc", "TaxableAmount"))
                taxable_amount.text = format_amount_for_xml(tax_subtotal.taxable_amount)
                taxable_amount.set("currencyID", tax_subtotal.currency_code)
                
                # TaxAmount
                tax_amount_sub = etree.SubElement(tax_subtotal_elem, self._qname("cbc", "TaxAmount"))
                tax_amount_sub.text = format_amount_for_xml(tax_subtotal.tax_amount)
                tax_amount_sub.set("currencyID", tax_subtotal.currency_code)
                
                # TaxCategory
                if tax_subtotal.tax_category:
                    tax_category = etree.SubElement(tax_subtotal_elem, self._qname("cac", "TaxCategory"))
                    
                    category_id = etree.SubElement(tax_category, self._qname("cbc", "ID"))
                    category_id.text = tax_subtotal.tax_category.tax_category_id
                    
                    if tax_subtotal.tax_category.tax_category_name:
                        category_name = etree.SubElement(tax_category, self._qname("cbc", "Name"))
                        category_name.text = tax_subtotal.tax_category.tax_category_name
                    
                    if tax_subtotal.tax_category.percent:
                        percent = etree.SubElement(tax_category, self._qname("cbc", "Percent"))
                        percent.text = format_percentage_for_xml(tax_subtotal.tax_category.percent)
                    
                    # TaxScheme
                    tax_scheme = etree.SubElement(tax_category, self._qname("cac", "TaxScheme"))
                    tax_scheme_id = etree.SubElement(tax_scheme, self._qname("cbc", "ID"))
                    tax_scheme_id.text = tax_subtotal.tax_category.tax_scheme_id
                    
                    if tax_subtotal.tax_category.tax_scheme_name:
                        tax_scheme_name = etree.SubElement(tax_scheme, self._qname("cbc", "Name"))
                        tax_scheme_name.text = tax_subtotal.tax_category.tax_scheme_name
    
    def _add_legal_monetary_total(self, root: etree.Element, invoice: UBLInvoice):
        """Add legal monetary total to XML."""
        
        if not invoice.legal_monetary_total:
            return
        
        monetary_total = etree.SubElement(root, self._qname("cac", "LegalMonetaryTotal"))
        
        # LineExtensionAmount
        line_extension = etree.SubElement(monetary_total, self._qname("cbc", "LineExtensionAmount"))
        line_extension.text = format_amount_for_xml(invoice.legal_monetary_total.line_extension_amount)
        line_extension.set("currencyID", invoice.legal_monetary_total.currency_code)
        
        # TaxExclusiveAmount
        tax_exclusive = etree.SubElement(monetary_total, self._qname("cbc", "TaxExclusiveAmount"))
        tax_exclusive.text = format_amount_for_xml(invoice.legal_monetary_total.tax_exclusive_amount)
        tax_exclusive.set("currencyID", invoice.legal_monetary_total.currency_code)
        
        # TaxInclusiveAmount
        tax_inclusive = etree.SubElement(monetary_total, self._qname("cbc", "TaxInclusiveAmount"))
        tax_inclusive.text = format_amount_for_xml(invoice.legal_monetary_total.tax_inclusive_amount)
        tax_inclusive.set("currencyID", invoice.legal_monetary_total.currency_code)
        
        # PayableAmount
        payable_amount = etree.SubElement(monetary_total, self._qname("cbc", "PayableAmount"))
        payable_amount.text = format_amount_for_xml(invoice.legal_monetary_total.payable_amount)
        payable_amount.set("currencyID", invoice.legal_monetary_total.currency_code)
    
    def _add_invoice_lines(self, root: etree.Element, invoice: UBLInvoice):
        """Add invoice lines to XML."""
        
        for line in invoice.invoice_lines:
            line_elem = etree.SubElement(root, self._qname("cac", "InvoiceLine"))
            
            # ID
            line_id = etree.SubElement(line_elem, self._qname("cbc", "ID"))
            line_id.text = line.line_id
            
            # InvoicedQuantity
            invoiced_quantity = etree.SubElement(line_elem, self._qname("cbc", "InvoicedQuantity"))
            invoiced_quantity.text = format_quantity_for_xml(line.invoiced_quantity)
            invoiced_quantity.set("unitCode", line.unit_code)
            
            # LineExtensionAmount
            line_extension = etree.SubElement(line_elem, self._qname("cbc", "LineExtensionAmount"))
            line_extension.text = format_amount_for_xml(line.line_extension_amount)
            line_extension.set("currencyID", line.currency_code)
            
            # Item
            item = etree.SubElement(line_elem, self._qname("cac", "Item"))
            
            if line.item_description:
                description = etree.SubElement(item, self._qname("cbc", "Description"))
                description.text = line.item_description
            
            if line.item_name:
                name = etree.SubElement(item, self._qname("cbc", "Name"))
                name.text = line.item_name
            
            # ClassifiedTaxCategory
            if line.tax_category:
                tax_category = etree.SubElement(item, self._qname("cac", "ClassifiedTaxCategory"))
                
                category_id = etree.SubElement(tax_category, self._qname("cbc", "ID"))
                category_id.text = line.tax_category.tax_category_id
                
                if line.tax_category.percent:
                    percent = etree.SubElement(tax_category, self._qname("cbc", "Percent"))
                    percent.text = format_percentage_for_xml(line.tax_category.percent)
                
                # TaxScheme
                tax_scheme = etree.SubElement(tax_category, self._qname("cac", "TaxScheme"))
                tax_scheme_id = etree.SubElement(tax_scheme, self._qname("cbc", "ID"))
                tax_scheme_id.text = line.tax_category.tax_scheme_id
            
            # Price
            if line.price:
                price = etree.SubElement(line_elem, self._qname("cac", "Price"))
                
                price_amount = etree.SubElement(price, self._qname("cbc", "PriceAmount"))
                price_amount.text = format_amount_for_xml(line.price.price_amount)
                price_amount.set("currencyID", line.price.currency_code)
                
                base_quantity = etree.SubElement(price, self._qname("cbc", "BaseQuantity"))
                base_quantity.text = format_quantity_for_xml(line.price.base_quantity)
                base_quantity.set("unitCode", line.price.unit_code)
    
    def _qname(self, prefix: str, localname: str) -> str:
        """Create qualified name for XML element."""
        if prefix in self.namespaces:
            return f"{{{self.namespaces[prefix]}}}{localname}"
        return localname
    
    def validate_xml(self, xml_string: str) -> bool:
        """Validate generated XML against UBL schema."""
        try:
            # Parse XML
            doc = etree.fromstring(xml_string.encode('utf-8'))
            
            # Basic validation - check required elements
            required_elements = [
                "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID",
                "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate",
                "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode"
            ]
            
            for element in required_elements:
                if doc.find(element) is None:
                    return False
            
            return True
            
        except etree.XMLSyntaxError:
            return False