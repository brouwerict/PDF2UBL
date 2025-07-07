"""Table extraction utilities for PDF processing."""

import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass
class TableCell:
    """Represents a cell in a table."""
    text: str
    x: float
    y: float
    width: float
    height: float
    row: int
    col: int


@dataclass
class ExtractedTable:
    """Represents an extracted table with metadata."""
    headers: List[str]
    rows: List[List[str]]
    table_type: str  # 'line_items', 'summary', 'unknown'
    confidence: float
    x: float
    y: float
    width: float
    height: float


class TableExtractor:
    """Advanced table extraction and analysis."""
    
    def __init__(self):
        self.line_item_headers = [
            'beschrijving', 'description', 'omschrijving', 'artikel', 'item',
            'aantal', 'quantity', 'qty', 'hoeveelheid',
            'prijs', 'price', 'bedrag', 'amount', 'unit price',
            'totaal', 'total', 'subtotal',
            'btw', 'vat', 'tax', 'belasting'
        ]
        
        self.summary_headers = [
            'subtotaal', 'subtotal', 'netto', 'net',
            'btw', 'vat', 'tax', 'belasting',
            'totaal', 'total', 'bruto', 'gross'
        ]
    
    def extract_tables(self, tables: List[List[List[str]]]) -> List[ExtractedTable]:
        """Extract and classify tables from raw table data.
        
        Args:
            tables: List of tables, each table is a list of rows, each row is a list of cells
            
        Returns:
            List of ExtractedTable objects
        """
        extracted_tables = []
        
        for i, table in enumerate(tables):
            if not table or not table[0]:
                continue
            
            # Extract headers and rows
            headers = self._clean_headers(table[0])
            rows = [self._clean_row(row) for row in table[1:] if row]
            
            # Classify table type
            table_type = self._classify_table(headers, rows)
            
            # Calculate confidence
            confidence = self._calculate_table_confidence(headers, rows, table_type)
            
            extracted_table = ExtractedTable(
                headers=headers,
                rows=rows,
                table_type=table_type,
                confidence=confidence,
                x=0,  # Would be filled with actual positioning data
                y=0,
                width=0,
                height=0
            )
            
            extracted_tables.append(extracted_table)
        
        return extracted_tables
    
    def extract_line_items(self, tables: List[ExtractedTable]) -> List[Dict[str, Any]]:
        """Extract line items from tables.
        
        Returns:
            List of line item dictionaries
        """
        line_items = []
        
        for table in tables:
            if table.table_type == 'line_items':
                items = self._process_line_items_table(table)
                line_items.extend(items)
        
        return line_items
    
    def extract_summary_data(self, tables: List[ExtractedTable]) -> Dict[str, Any]:
        """Extract summary financial data from tables.
        
        Returns:
            Dictionary with summary data
        """
        summary_data = {
            'subtotal': None,
            'vat_amount': None,
            'total_amount': None,
            'vat_rate': None
        }
        
        for table in tables:
            if table.table_type == 'summary':
                data = self._process_summary_table(table)
                summary_data.update(data)
        
        return summary_data
    
    def _clean_headers(self, headers: List[str]) -> List[str]:
        """Clean and normalize table headers."""
        cleaned = []
        for header in headers:
            if header:
                # Remove extra whitespace and convert to lowercase
                cleaned_header = re.sub(r'\s+', ' ', header.strip().lower())
                cleaned.append(cleaned_header)
            else:
                cleaned.append('')
        return cleaned
    
    def _clean_row(self, row: List[str]) -> List[str]:
        """Clean table row data."""
        cleaned = []
        for cell in row:
            if cell:
                # Remove extra whitespace
                cleaned_cell = re.sub(r'\s+', ' ', cell.strip())
                cleaned.append(cleaned_cell)
            else:
                cleaned.append('')
        return cleaned
    
    def _classify_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Classify table type based on headers and content."""
        
        # Check for line items table
        line_item_score = 0
        for header in headers:
            if any(indicator in header.lower() for indicator in self.line_item_headers):
                line_item_score += 1
        
        # Check for summary table
        summary_score = 0
        for header in headers:
            if any(indicator in header.lower() for indicator in self.summary_headers):
                summary_score += 1
        
        # Also check row content for classification
        if rows:
            # Look for numeric content (typical in both types)
            numeric_content = sum(1 for row in rows for cell in row if self._is_numeric(cell))
            total_content = sum(len(row) for row in rows)
            
            if total_content > 0:
                numeric_ratio = numeric_content / total_content
                
                # High numeric ratio + multiple rows = likely line items
                if numeric_ratio > 0.3 and len(rows) > 2:
                    line_item_score += 2
                
                # High numeric ratio + few rows = likely summary
                elif numeric_ratio > 0.5 and len(rows) <= 3:
                    summary_score += 2
        
        # Determine table type
        if line_item_score > summary_score and line_item_score > 0:
            return 'line_items'
        elif summary_score > 0:
            return 'summary'
        else:
            return 'unknown'
    
    def _calculate_table_confidence(self, headers: List[str], rows: List[List[str]], table_type: str) -> float:
        """Calculate confidence score for table classification."""
        confidence = 0.5
        
        # Base confidence on header recognition
        recognized_headers = 0
        all_indicators = self.line_item_headers + self.summary_headers
        
        for header in headers:
            if any(indicator in header.lower() for indicator in all_indicators):
                recognized_headers += 1
        
        if headers:
            header_ratio = recognized_headers / len(headers)
            confidence += header_ratio * 0.3
        
        # Adjust based on table type
        if table_type == 'line_items':
            # Higher confidence for tables with multiple rows
            if len(rows) > 2:
                confidence += 0.2
            
            # Check for typical line item patterns
            if self._has_line_item_patterns(rows):
                confidence += 0.2
        
        elif table_type == 'summary':
            # Higher confidence for tables with totals
            if self._has_total_patterns(rows):
                confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _process_line_items_table(self, table: ExtractedTable) -> List[Dict[str, Any]]:
        """Process a line items table into structured data."""
        line_items = []
        
        # Map headers to expected fields
        header_mapping = self._map_line_item_headers(table.headers)
        
        for row in table.rows:
            if not any(row):  # Skip empty rows
                continue
            
            line_item = {}
            
            for i, cell in enumerate(row):
                if i < len(table.headers):
                    field_name = header_mapping.get(i)
                    if field_name:
                        line_item[field_name] = self._parse_cell_value(cell, field_name)
            
            # Only add if we have at least a description
            if line_item.get('description'):
                line_items.append(line_item)
        
        return line_items
    
    def _process_summary_table(self, table: ExtractedTable) -> Dict[str, Any]:
        """Process a summary table into structured data."""
        summary = {}
        
        # Look for key-value pairs in the table
        for row in table.rows:
            if len(row) >= 2:
                key = row[0].lower().strip()
                value = row[1].strip()
                
                # Map common summary fields
                if any(indicator in key for indicator in ['subtotal', 'subtotaal', 'netto']):
                    summary['subtotal'] = self._parse_amount(value)
                
                elif any(indicator in key for indicator in ['btw', 'vat', 'tax']):
                    if '%' in value:
                        summary['vat_rate'] = self._parse_percentage(value)
                    else:
                        summary['vat_amount'] = self._parse_amount(value)
                
                elif any(indicator in key for indicator in ['totaal', 'total', 'bruto']):
                    summary['total_amount'] = self._parse_amount(value)
        
        return summary
    
    def _map_line_item_headers(self, headers: List[str]) -> Dict[int, str]:
        """Map table column indices to field names."""
        mapping = {}
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            
            if any(indicator in header_lower for indicator in ['beschrijving', 'description', 'omschrijving']):
                mapping[i] = 'description'
            
            elif any(indicator in header_lower for indicator in ['aantal', 'quantity', 'qty']):
                mapping[i] = 'quantity'
            
            elif any(indicator in header_lower for indicator in ['prijs', 'price', 'unit']):
                mapping[i] = 'unit_price'
            
            elif any(indicator in header_lower for indicator in ['totaal', 'total', 'bedrag']):
                mapping[i] = 'total_amount'
            
            elif any(indicator in header_lower for indicator in ['btw', 'vat', 'tax']):
                mapping[i] = 'vat_rate'
        
        return mapping
    
    def _parse_cell_value(self, cell: str, field_name: str) -> Any:
        """Parse cell value based on expected field type."""
        if not cell:
            return None
        
        if field_name in ['quantity', 'unit_price', 'total_amount']:
            return self._parse_amount(cell)
        
        elif field_name == 'vat_rate':
            if '%' in cell:
                return self._parse_percentage(cell)
            else:
                return self._parse_amount(cell)
        
        else:
            return cell.strip()
    
    def _parse_amount(self, text: str) -> Optional[float]:
        """Parse monetary amount from text."""
        if not text:
            return None
        
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[€$£\s]', '', text)
        
        # Handle comma as decimal separator
        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')
        elif ',' in cleaned and '.' in cleaned:
            # Handle format like "1.234,56" (European format)
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
        
        # Extract numeric value
        match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        return None
    
    def _parse_percentage(self, text: str) -> Optional[float]:
        """Parse percentage from text."""
        if not text:
            return None
        
        # Extract numeric value before %
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*%', text)
        if match:
            try:
                value = match.group(1).replace(',', '.')
                return float(value)
            except ValueError:
                return None
        
        return None
    
    def _is_numeric(self, text: str) -> bool:
        """Check if text contains numeric value."""
        if not text:
            return False
        
        # Check for numbers, currency symbols, percentages
        return bool(re.search(r'[\d€$£%]', text))
    
    def _has_line_item_patterns(self, rows: List[List[str]]) -> bool:
        """Check if rows contain typical line item patterns."""
        if not rows:
            return False
        
        # Look for numeric values in multiple columns (typical of line items)
        numeric_columns = set()
        for row in rows:
            for i, cell in enumerate(row):
                if self._is_numeric(cell):
                    numeric_columns.add(i)
        
        return len(numeric_columns) >= 2
    
    def _has_total_patterns(self, rows: List[List[str]]) -> bool:
        """Check if rows contain typical total/summary patterns."""
        if not rows:
            return False
        
        # Look for words indicating totals
        total_indicators = ['totaal', 'total', 'subtotal', 'subtotaal', 'btw', 'vat']
        
        for row in rows:
            for cell in row:
                if cell and any(indicator in cell.lower() for indicator in total_indicators):
                    return True
        
        return False