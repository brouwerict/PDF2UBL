"""ML-powered pattern analyzer for PDF2UBL."""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import string

logger = logging.getLogger(__name__)

@dataclass
class PatternAnalysisResult:
    """Result of pattern analysis."""
    suggested_patterns: List[Dict[str, Any]]
    confidence_scores: List[float]
    pattern_coverage: float
    recommendations: List[str]

class PatternAnalyzer:
    """ML-powered pattern analyzer for extraction rules."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common pattern templates for different field types
        self.pattern_templates = {
            "text": [
                r'([A-Za-z0-9\s\-\.]+)',
                r'([A-Z][a-z\s]+)',
                r'([A-Z0-9\-/]+)',
                r'([^\n\r]+)'
            ],
            "number": [
                r'(\d+)',
                r'(\d+[.,]\d+)',
                r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})'
            ],
            "date": [
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(\d{2}-\d{2}-\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{4}-\d{2}-\d{2})'
            ],
            "amount": [
                r'€?\s*(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2})\s*€?',
                r'€\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})',
                r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s*EUR?'
            ],
            "vat_number": [
                r'([A-Z]{2}\d{9}B\d{2})',
                r'([A-Z]{2}\s*\d{9}\s*B\s*\d{2})',
                r'(NL\d{9}B\d{2})'
            ],
            "email": [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'([^\s@]+@[^\s@]+\.[^\s@]+)'
            ],
            "phone": [
                r'(\+31\s*\d{1,3}\s*\d{3}\s*\d{4})',
                r'(0\d{1,3}\s*\d{3}\s*\d{4})',
                r'(\+\d{1,4}\s*\d{3,4}\s*\d{4,6})'
            ]
        }
        
        # Common keywords for different field types in Dutch/English
        self.field_keywords = {
            "invoice_number": ["factuur", "invoice", "nummer", "number", "nr", "fact"],
            "invoice_date": ["datum", "date", "factuurdatum", "invoice date"],
            "total_amount": ["totaal", "total", "te betalen", "to pay", "bedrag", "amount"],
            "net_amount": ["subtotaal", "subtotal", "netto", "net", "excl", "exclusief"],
            "vat_amount": ["btw", "vat", "tax", "belasting"],
            "supplier_name": ["leverancier", "supplier", "van", "from", "factureren"],
            "supplier_vat_number": ["btw", "vat", "nummer", "number"],
            "due_date": ["vervaldatum", "due date", "betaaldatum", "payment date"]
        }
    
    def analyze_patterns(self, 
                        text_samples: List[str],
                        field_type: str,
                        existing_patterns: List[str] = None) -> PatternAnalysisResult:
        """Analyze text samples to suggest extraction patterns."""
        
        self.logger.info(f"Analyzing patterns for field type: {field_type}")
        
        if not text_samples:
            raise ValueError("At least one text sample is required")
        
        existing_patterns = existing_patterns or []
        
        # Extract potential values for the field type
        potential_values = self._extract_potential_values(text_samples, field_type)
        
        if not potential_values:
            return PatternAnalysisResult(
                suggested_patterns=[],
                confidence_scores=[],
                pattern_coverage=0.0,
                recommendations=[f"No values found for field type '{field_type}'. Consider different sample texts."]
            )
        
        # Generate patterns for the potential values
        suggested_patterns = self._generate_patterns(potential_values, field_type, text_samples)
        
        # Filter out existing patterns
        new_patterns = []
        for pattern_data in suggested_patterns:
            if pattern_data["pattern"] not in existing_patterns:
                new_patterns.append(pattern_data)
        
        # Calculate confidence scores
        confidence_scores = [p["confidence"] for p in new_patterns]
        
        # Calculate pattern coverage
        coverage = self._calculate_coverage(new_patterns, text_samples, field_type)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(new_patterns, coverage, field_type)
        
        return PatternAnalysisResult(
            suggested_patterns=new_patterns,
            confidence_scores=confidence_scores,
            pattern_coverage=coverage,
            recommendations=recommendations
        )
    
    def _extract_potential_values(self, text_samples: List[str], field_type: str) -> List[str]:
        """Extract potential values for the given field type from text samples."""
        
        potential_values = []
        
        # Get pattern templates for the field type
        templates = self.pattern_templates.get(field_type, self.pattern_templates["text"])
        
        for text in text_samples:
            for template in templates:
                matches = re.findall(template, text, re.IGNORECASE | re.MULTILINE)
                potential_values.extend(matches)
        
        # Remove duplicates and filter by quality
        unique_values = list(set(potential_values))
        filtered_values = self._filter_values_by_quality(unique_values, field_type)
        
        return filtered_values[:20]  # Limit to top 20 values
    
    def _filter_values_by_quality(self, values: List[str], field_type: str) -> List[str]:
        """Filter values based on quality criteria for the field type."""
        
        filtered = []
        
        for value in values:
            value = value.strip()
            
            if not value or len(value) < 2:
                continue
            
            # Field-specific quality filters
            if field_type == "amount":
                # Must contain digits and reasonable length
                if re.search(r'\d', value) and len(value) <= 15:
                    filtered.append(value)
            
            elif field_type == "date":
                # Must look like a date
                if re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', value):
                    filtered.append(value)
            
            elif field_type == "vat_number":
                # Must match VAT number format
                if re.match(r'[A-Z]{2}\d{9}B\d{2}', value):
                    filtered.append(value)
            
            elif field_type == "email":
                # Must contain @ and domain
                if '@' in value and '.' in value:
                    filtered.append(value)
            
            elif field_type == "phone":
                # Must contain enough digits
                digits = re.findall(r'\d', value)
                if len(digits) >= 8:
                    filtered.append(value)
            
            elif field_type == "text":
                # General text quality filters
                if len(value) <= 100 and not value.isdigit():
                    filtered.append(value)
            
            else:
                # Default: reasonable length
                if 2 <= len(value) <= 100:
                    filtered.append(value)
        
        return filtered
    
    def _generate_patterns(self, values: List[str], field_type: str, text_samples: List[str]) -> List[Dict[str, Any]]:
        """Generate regex patterns for the given values."""
        
        patterns = []
        
        # Generate specific patterns for each value
        for value in values:
            pattern_data = self._create_pattern_for_value(value, field_type, text_samples)
            if pattern_data:
                patterns.append(pattern_data)
        
        # Generate generalized patterns
        generalized_patterns = self._create_generalized_patterns(values, field_type, text_samples)
        patterns.extend(generalized_patterns)
        
        # Remove duplicates and sort by confidence
        unique_patterns = {}
        for pattern_data in patterns:
            pattern = pattern_data["pattern"]
            if pattern not in unique_patterns or pattern_data["confidence"] > unique_patterns[pattern]["confidence"]:
                unique_patterns[pattern] = pattern_data
        
        result = list(unique_patterns.values())
        result.sort(key=lambda x: x["confidence"], reverse=True)
        
        return result[:10]  # Return top 10 patterns
    
    def _create_pattern_for_value(self, value: str, field_type: str, text_samples: List[str]) -> Optional[Dict[str, Any]]:
        """Create a regex pattern for a specific value."""
        
        # Look for context around the value in samples
        context_patterns = []
        
        for text in text_samples:
            # Find all occurrences of the value
            escaped_value = re.escape(value)
            matches = re.finditer(escaped_value, text, re.IGNORECASE)
            
            for match in matches:
                start, end = match.span()
                
                # Get context before and after
                before = text[max(0, start-50):start].strip()
                after = text[end:end+50].strip()
                
                # Look for keywords in the context
                keywords = self.field_keywords.get(field_type, [])
                
                for keyword in keywords:
                    if keyword.lower() in before.lower():
                        # Create pattern with keyword context
                        keyword_pattern = rf'{re.escape(keyword)}[:\s]*({escaped_value})'
                        context_patterns.append(keyword_pattern)
                    
                    elif keyword.lower() in after.lower():
                        # Create pattern with value before keyword
                        keyword_pattern = rf'({escaped_value})[:\s]*{re.escape(keyword)}'
                        context_patterns.append(keyword_pattern)
        
        # If no context found, create a simple pattern
        if not context_patterns:
            simple_pattern = f'({re.escape(value)})'
            confidence = 0.3  # Low confidence for patterns without context
        else:
            # Use the most common context pattern
            pattern_counts = Counter(context_patterns)
            simple_pattern = pattern_counts.most_common(1)[0][0]
            confidence = 0.7  # Higher confidence for patterns with context
        
        # Test pattern against samples
        test_confidence = self._test_pattern_confidence(simple_pattern, text_samples)
        final_confidence = (confidence + test_confidence) / 2
        
        if final_confidence < 0.2:
            return None
        
        return {
            "pattern": simple_pattern,
            "method": "regex",
            "field_type": field_type,
            "confidence": final_confidence,
            "name": f"Pattern for '{value[:20]}{'...' if len(value) > 20 else ''}'",
            "description": f"Specific pattern for value: {value}",
            "example_value": value
        }
    
    def _create_generalized_patterns(self, values: List[str], field_type: str, text_samples: List[str]) -> List[Dict[str, Any]]:
        """Create generalized patterns based on value analysis."""
        
        generalized = []
        
        # Analyze value characteristics
        characteristics = self._analyze_value_characteristics(values, field_type)
        
        # Create patterns based on characteristics
        for char_type, char_data in characteristics.items():
            if char_data["count"] >= 2:  # At least 2 values with this characteristic
                pattern_data = self._create_pattern_from_characteristic(char_type, char_data, field_type, text_samples)
                if pattern_data:
                    generalized.append(pattern_data)
        
        return generalized
    
    def _analyze_value_characteristics(self, values: List[str], field_type: str) -> Dict[str, Dict[str, Any]]:
        """Analyze characteristics of values to create generalized patterns."""
        
        characteristics = {}
        
        # Analyze length patterns
        lengths = [len(v) for v in values]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            min_length = min(lengths)
            max_length = max(lengths)
            
            characteristics["length"] = {
                "count": len(values),
                "avg": avg_length,
                "min": min_length,
                "max": max_length,
                "pattern_type": "length"
            }
        
        # Analyze character patterns
        if field_type == "text":
            # Check for uppercase/lowercase patterns
            uppercase_count = sum(1 for v in values if v.isupper())
            if uppercase_count >= len(values) * 0.5:
                characteristics["uppercase"] = {
                    "count": uppercase_count,
                    "pattern_type": "case",
                    "case": "upper"
                }
            
            lowercase_count = sum(1 for v in values if v.islower())
            if lowercase_count >= len(values) * 0.5:
                characteristics["lowercase"] = {
                    "count": lowercase_count,
                    "pattern_type": "case",
                    "case": "lower"
                }
            
            # Check for alphanumeric patterns
            alphanum_count = sum(1 for v in values if v.isalnum())
            if alphanum_count >= len(values) * 0.5:
                characteristics["alphanumeric"] = {
                    "count": alphanum_count,
                    "pattern_type": "character_class"
                }
        
        # Analyze number patterns
        elif field_type in ["amount", "number"]:
            # Check for decimal patterns
            decimal_count = sum(1 for v in values if ',' in v or '.' in v)
            if decimal_count >= len(values) * 0.5:
                characteristics["decimal"] = {
                    "count": decimal_count,
                    "pattern_type": "decimal"
                }
        
        # Analyze date patterns
        elif field_type == "date":
            # Check for different date formats
            formats = {
                "dd-mm-yyyy": r'\d{2}-\d{2}-\d{4}',
                "dd/mm/yyyy": r'\d{2}/\d{2}/\d{4}',
                "d-m-yyyy": r'\d{1,2}-\d{1,2}-\d{4}',
                "yyyy-mm-dd": r'\d{4}-\d{2}-\d{2}'
            }
            
            for format_name, format_pattern in formats.items():
                format_count = sum(1 for v in values if re.match(format_pattern, v))
                if format_count >= len(values) * 0.3:
                    characteristics[format_name] = {
                        "count": format_count,
                        "pattern_type": "date_format",
                        "format": format_name
                    }
        
        return characteristics
    
    def _create_pattern_from_characteristic(self, char_type: str, char_data: Dict[str, Any], field_type: str, text_samples: List[str]) -> Optional[Dict[str, Any]]:
        """Create a regex pattern from value characteristic analysis."""
        
        pattern_type = char_data.get("pattern_type")
        
        if pattern_type == "length":
            min_len = char_data["min"]
            max_len = char_data["max"]
            
            if field_type == "text":
                pattern = rf'([A-Za-z0-9\s\-\.]{{{min_len},{max_len}}})'
            elif field_type == "amount":
                pattern = rf'(\d{{1,{max_len-2}}}[.,]\d{{2}})'
            else:
                pattern = rf'(.{{{min_len},{max_len}}})'
        
        elif pattern_type == "case" and char_data["case"] == "upper":
            pattern = r'([A-Z0-9\-/]+)'
        
        elif pattern_type == "case" and char_data["case"] == "lower":
            pattern = r'([a-z0-9\s\-\.]+)'
        
        elif pattern_type == "character_class":
            pattern = r'([A-Za-z0-9]+)'
        
        elif pattern_type == "decimal":
            pattern = r'(\d+[.,]\d{2})'
        
        elif pattern_type == "date_format":
            format_name = char_data["format"]
            if format_name == "dd-mm-yyyy":
                pattern = r'(\d{2}-\d{2}-\d{4})'
            elif format_name == "dd/mm/yyyy":
                pattern = r'(\d{2}/\d{2}/\d{4})'
            elif format_name == "d-m-yyyy":
                pattern = r'(\d{1,2}-\d{1,2}-\d{4})'
            elif format_name == "yyyy-mm-dd":
                pattern = r'(\d{4}-\d{2}-\d{2})'
            else:
                pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        
        else:
            return None
        
        # Test pattern confidence
        confidence = self._test_pattern_confidence(pattern, text_samples)
        
        if confidence < 0.3:
            return None
        
        return {
            "pattern": pattern,
            "method": "regex",
            "field_type": field_type,
            "confidence": confidence,
            "name": f"Generalized {char_type} pattern",
            "description": f"Pattern based on {char_type} analysis",
            "characteristic": char_type
        }
    
    def _test_pattern_confidence(self, pattern: str, text_samples: List[str]) -> float:
        """Test pattern against text samples and return confidence score."""
        
        try:
            matches = 0
            total_samples = len(text_samples)
            
            for text in text_samples:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    matches += 1
            
            return matches / total_samples if total_samples > 0 else 0.0
        
        except re.error:
            return 0.0
    
    def _calculate_coverage(self, patterns: List[Dict[str, Any]], text_samples: List[str], field_type: str) -> float:
        """Calculate how well the patterns cover the text samples."""
        
        if not patterns or not text_samples:
            return 0.0
        
        covered_samples = 0
        
        for text in text_samples:
            sample_covered = False
            
            for pattern_data in patterns:
                pattern = pattern_data["pattern"]
                try:
                    if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                        sample_covered = True
                        break
                except re.error:
                    continue
            
            if sample_covered:
                covered_samples += 1
        
        return covered_samples / len(text_samples)
    
    def _generate_recommendations(self, patterns: List[Dict[str, Any]], coverage: float, field_type: str) -> List[str]:
        """Generate recommendations based on pattern analysis."""
        
        recommendations = []
        
        if not patterns:
            recommendations.append(f"No patterns found for field type '{field_type}'. Consider providing more diverse sample texts.")
            recommendations.append("Try using samples from different suppliers or document formats.")
        
        elif coverage < 0.5:
            recommendations.append(f"Pattern coverage is low ({coverage:.1%}). Consider adding more patterns or improving existing ones.")
            recommendations.append("Review the sample texts to ensure they contain the target field type.")
        
        elif coverage < 0.8:
            recommendations.append(f"Pattern coverage is moderate ({coverage:.1%}). Consider refining patterns for better accuracy.")
        
        else:
            recommendations.append(f"Good pattern coverage ({coverage:.1%}). The suggested patterns should work well.")
        
        # Pattern-specific recommendations
        high_confidence_patterns = [p for p in patterns if p["confidence"] > 0.7]
        if len(high_confidence_patterns) < len(patterns) * 0.5:
            recommendations.append("Some patterns have low confidence. Consider testing with more sample data.")
        
        if len(patterns) > 5:
            recommendations.append("Many patterns found. Consider using only the top-rated ones to avoid conflicts.")
        
        # Field-specific recommendations
        if field_type == "amount" and patterns:
            recommendations.append("For amount fields, ensure patterns capture both the value and currency symbol.")
        
        elif field_type == "date" and patterns:
            recommendations.append("For date fields, test patterns with different date formats found in your documents.")
        
        elif field_type == "vat_number" and patterns:
            recommendations.append("For VAT numbers, ensure patterns strictly match the required format (NL000000000B00).")
        
        return recommendations