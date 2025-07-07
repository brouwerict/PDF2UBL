"""Main PDF extraction module."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime
import fitz  # PyMuPDF
import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class ExtractedInvoiceData:
    """Container for extracted invoice data."""
    
    # Basic invoice information
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Supplier information
    supplier_name: Optional[str] = None
    supplier_address: Optional[str] = None
    supplier_vat_number: Optional[str] = None
    supplier_iban: Optional[str] = None
    
    # Customer information
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_vat_number: Optional[str] = None
    
    # Financial information
    total_amount: Optional[float] = None
    vat_amount: Optional[float] = None
    net_amount: Optional[float] = None
    currency: str = "EUR"
    
    # Line items
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    
    # Tables (raw)
    tables: List[List[List[str]]] = field(default_factory=list)
    
    # Confidence scores
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    # Raw text for fallback
    raw_text: str = ""
    
    # Positioned text data (for advanced pattern matching)
    positioned_text: Optional[Dict[str, Any]] = None
    
    # Metadata
    extraction_method: str = "default"
    processing_timestamp: datetime = field(default_factory=datetime.now)


class PDFExtractor:
    """Main PDF extractor class that coordinates different extraction methods."""
    
    def __init__(self, use_ocr: bool = False, language: str = "nld"):
        """Initialize PDF extractor.
        
        Args:
            use_ocr: Whether to use OCR for scanned PDFs
            language: Language code for OCR (default: Dutch)
        """
        self.use_ocr = use_ocr
        self.language = language
        self.logger = logging.getLogger(__name__)
    
    def extract(self, pdf_path: Union[str, Path]) -> ExtractedInvoiceData:
        """Extract invoice data from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ExtractedInvoiceData: Container with extracted data
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.logger.info(f"Extracting data from {pdf_path}")
        
        # Try multiple extraction methods
        data = ExtractedInvoiceData()
        
        # Method 1: Try pdfplumber first (best for tables)
        try:
            data = self._extract_with_pdfplumber(pdf_path)
            data.extraction_method = "pdfplumber"
            self.logger.info("Successfully extracted with pdfplumber")
        except Exception as e:
            self.logger.warning(f"pdfplumber extraction failed: {e}")
            
            # Method 2: Fallback to PyMuPDF
            try:
                data = self._extract_with_pymupdf(pdf_path)
                data.extraction_method = "pymupdf"
                self.logger.info("Successfully extracted with PyMuPDF")
            except Exception as e:
                self.logger.error(f"PyMuPDF extraction failed: {e}")
                
                # Method 3: OCR fallback (if enabled)
                if self.use_ocr:
                    try:
                        data = self._extract_with_ocr(pdf_path)
                        data.extraction_method = "ocr"
                        self.logger.info("Successfully extracted with OCR")
                    except Exception as e:
                        self.logger.error(f"OCR extraction failed: {e}")
                        raise Exception("All extraction methods failed")
        
        # Post-process extracted data
        self._post_process_data(data)
        
        return data
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> ExtractedInvoiceData:
        """Extract using pdfplumber (good for tables and structured text)."""
        data = ExtractedInvoiceData()
        
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from all pages
            all_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"
                
                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    if table:  # Only process non-empty tables
                        data.tables.append(table)
                        self._process_table(table, data)
            
            data.raw_text = all_text
            
            # Extract basic information using regex patterns
            self._extract_basic_info(all_text, data)
        
        return data
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> ExtractedInvoiceData:
        """Extract using PyMuPDF (good for text positioning)."""
        data = ExtractedInvoiceData()
        
        doc = fitz.open(pdf_path)
        all_text = ""
        
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                all_text += page_text + "\n"
                
                # Get text with positioning information
                text_dict = page.get_text("dict")
                self._process_positioned_text(text_dict, data)
            
            data.raw_text = all_text
            self._extract_basic_info(all_text, data)
            
        finally:
            doc.close()
        
        return data
    
    def _extract_with_ocr(self, pdf_path: Path) -> ExtractedInvoiceData:
        """Extract using OCR (fallback for scanned PDFs)."""
        # This would require additional OCR libraries like tesseract
        # For now, return empty data with a note
        data = ExtractedInvoiceData()
        data.raw_text = "OCR extraction not yet implemented"
        return data
    
    def _extract_basic_info(self, text: str, data: ExtractedInvoiceData):
        """Extract basic invoice information using regex patterns."""
        
        # Invoice number patterns
        invoice_patterns = [
            r'factuur(?:nummer)?[:\s#-]*(\w+)',
            r'invoice(?:\s+number)?[:\s#-]*(\w+)',
            r'nr[:\s.]*(\w+)',
            r'nummer[:\s]*(\w+)',
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data.invoice_number = match.group(1)
                data.confidence_scores['invoice_number'] = 0.8
                break
        
        # Date patterns
        date_patterns = [
            r'datum[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Try to parse date (basic implementation)
                    for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y']:
                        try:
                            data.invoice_date = datetime.strptime(date_str, fmt)
                            data.confidence_scores['invoice_date'] = 0.7
                            break
                        except ValueError:
                            continue
                    if data.invoice_date:
                        break
                except Exception:
                    continue
        
        # Amount patterns
        amount_patterns = [
            r'totaal[:\s]*€?\s*(\d+[.,]\d{2})',
            r'total[:\s]*€?\s*(\d+[.,]\d{2})',
            r'bedrag[:\s]*€?\s*(\d+[.,]\d{2})',
            r'€\s*(\d+[.,]\d{2})',
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Take the last/largest amount found
                amounts = []
                for match in matches:
                    try:
                        amount_str = match.replace(',', '.')
                        amounts.append(float(amount_str))
                    except ValueError:
                        continue
                
                if amounts:
                    data.total_amount = max(amounts)
                    data.confidence_scores['total_amount'] = 0.6
                    break
        
        # VAT number patterns
        vat_patterns = [
            r'btw[:\s-]*(?:nr|nummer)?[:\s]*([A-Z]{2}\d{9}B\d{2})',
            r'vat[:\s-]*(?:nr|number)?[:\s]*([A-Z]{2}\d{9}B\d{2})',
        ]
        
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data.supplier_vat_number = match.group(1)
                data.confidence_scores['supplier_vat_number'] = 0.9
                break
        
        # Company name (first line usually)
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 3 and not re.match(r'^\d', line):
                if not data.supplier_name:
                    data.supplier_name = line
                    data.confidence_scores['supplier_name'] = 0.5
                    break
    
    def _process_table(self, table: List[List[str]], data: ExtractedInvoiceData):
        """Process extracted table data."""
        if not table:
            return
        
        # Try to identify if this is a line items table
        header = table[0] if table else []
        
        # Look for typical invoice line item headers
        line_item_indicators = [
            'beschrijving', 'description', 'omschrijving',
            'aantal', 'quantity', 'qty',
            'prijs', 'price', 'bedrag', 'amount'
        ]
        
        has_line_items = any(
            any(indicator in cell.lower() for indicator in line_item_indicators)
            for cell in header if cell
        )
        
        if has_line_items:
            # Process as line items table
            for row in table[1:]:  # Skip header
                if len(row) >= 2:
                    line_item = {
                        'description': row[0] if row[0] else '',
                        'quantity': self._extract_number(row[1]) if len(row) > 1 else 1,
                        'unit_price': self._extract_number(row[2]) if len(row) > 2 else 0,
                        'total_amount': self._extract_number(row[3]) if len(row) > 3 else 0,
                    }
                    data.line_items.append(line_item)
    
    def _process_positioned_text(self, text_dict: Dict, data: ExtractedInvoiceData):
        """Process text with positioning information from PyMuPDF."""
        # This could be enhanced to use text positioning for better extraction
        # For now, just extract text content
        pass
    
    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text."""
        if not text:
            return 0.0
        
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[€$£\s]', '', text)
        
        # Handle comma as decimal separator
        cleaned = cleaned.replace(',', '.')
        
        # Extract number
        match = re.search(r'(\d+(?:\.\d{2})?)', cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _post_process_data(self, data: ExtractedInvoiceData):
        """Post-process extracted data for validation and cleanup."""
        
        # Validate and clean invoice number
        if data.invoice_number:
            data.invoice_number = re.sub(r'[^\w\-/]', '', data.invoice_number)
        
        # Validate amounts
        if data.total_amount and data.total_amount < 0:
            data.total_amount = abs(data.total_amount)
        
        # Calculate missing amounts if possible
        if data.line_items:
            calculated_total = sum(item.get('total_amount', 0) for item in data.line_items)
            if calculated_total > 0 and not data.total_amount:
                data.total_amount = calculated_total
                data.confidence_scores['total_amount'] = 0.8
        
        # Clean supplier name
        if data.supplier_name:
            data.supplier_name = data.supplier_name.strip()
            # Remove common prefixes/suffixes
            data.supplier_name = re.sub(r'^(van|de|het|b\.?v\.?|ltd\.?|inc\.?)\s+', '', data.supplier_name, flags=re.IGNORECASE)
    
    def get_extraction_quality(self, data: ExtractedInvoiceData) -> float:
        """Calculate overall extraction quality score."""
        scores = []
        
        # Check for presence of key fields
        if data.invoice_number:
            scores.append(data.confidence_scores.get('invoice_number', 0.5))
        
        if data.invoice_date:
            scores.append(data.confidence_scores.get('invoice_date', 0.5))
        
        if data.total_amount:
            scores.append(data.confidence_scores.get('total_amount', 0.5))
        
        if data.supplier_name:
            scores.append(data.confidence_scores.get('supplier_name', 0.5))
        
        return sum(scores) / len(scores) if scores else 0.0