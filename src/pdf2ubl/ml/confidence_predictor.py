"""ML-powered confidence predictor for PDF2UBL."""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics

from ..templates.template_models import Template, FieldPattern, ExtractionRule

logger = logging.getLogger(__name__)

@dataclass
class ConfidencePredictionResult:
    """Result of confidence prediction."""
    overall_confidence: float
    field_confidences: Dict[str, float]
    quality_score: float
    recommendations: List[str]

class ConfidencePredictor:
    """ML-powered confidence predictor for extraction quality."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Quality scoring weights
        self.quality_weights = {
            "pattern_specificity": 0.25,
            "pattern_coverage": 0.25,
            "field_completeness": 0.20,
            "text_quality": 0.15,
            "template_maturity": 0.15
        }
        
        # Field importance weights (for overall confidence calculation)
        self.field_importance = {
            "invoice_number": 0.20,
            "invoice_date": 0.20,
            "total_amount": 0.20,
            "supplier_name": 0.15,
            "supplier_vat_number": 0.10,
            "net_amount": 0.05,
            "vat_amount": 0.05,
            "currency": 0.03,
            "due_date": 0.02
        }
    
    def predict_confidence(self, template: Template, text_content: str) -> ConfidencePredictionResult:
        """Predict extraction confidence for given text and template."""
        
        self.logger.info(f"Predicting confidence for template: {template.name}")
        
        # Calculate field-level confidences
        field_confidences = self._calculate_field_confidences(template, text_content)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(field_confidences, template)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(template, text_content, field_confidences)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(template, text_content, field_confidences, quality_score)
        
        return ConfidencePredictionResult(
            overall_confidence=overall_confidence,
            field_confidences=field_confidences,
            quality_score=quality_score,
            recommendations=recommendations
        )
    
    def _calculate_field_confidences(self, template: Template, text_content: str) -> Dict[str, float]:
        """Calculate confidence scores for each field in the template."""
        
        field_confidences = {}
        
        # Test each extraction rule
        for rule in template.extraction_rules:
            confidence = self._test_extraction_rule(rule, text_content)
            field_confidences[rule.field_name] = confidence
        
        return field_confidences
    
    def _test_extraction_rule(self, rule: ExtractionRule, text_content: str) -> float:
        """Test an extraction rule against text content and return confidence."""
        
        if not rule.patterns:
            return 0.0
        
        pattern_scores = []
        
        for pattern in rule.patterns:
            score = self._test_pattern(pattern, text_content)
            pattern_scores.append(score)
        
        if not pattern_scores:
            return 0.0
        
        # Use the highest scoring pattern, but consider pattern diversity
        max_score = max(pattern_scores)
        avg_score = statistics.mean(pattern_scores)
        
        # Weighted combination favoring the best pattern but rewarding consistency
        final_score = (max_score * 0.7) + (avg_score * 0.3)
        
        return min(final_score, 1.0)
    
    def _test_pattern(self, pattern: FieldPattern, text_content: str) -> float:
        """Test a single pattern against text content."""
        
        try:
            # Test if pattern matches
            flags = 0
            if not pattern.case_sensitive:
                flags |= re.IGNORECASE
            if pattern.multiline:
                flags |= re.MULTILINE
            
            match = re.search(pattern.pattern, text_content, flags)
            
            if not match:
                return 0.0
            
            # Base confidence from pattern
            confidence = pattern.confidence_threshold
            
            # Adjust based on match quality
            confidence = self._adjust_confidence_by_match_quality(pattern, match, text_content)
            
            # Adjust based on pattern specificity
            confidence = self._adjust_confidence_by_specificity(pattern, confidence)
            
            # Adjust based on context
            confidence = self._adjust_confidence_by_context(pattern, match, text_content)
            
            return min(confidence, 1.0)
        
        except re.error as e:
            self.logger.warning(f"Invalid regex pattern: {pattern.pattern} - {e}")
            return 0.0
    
    def _adjust_confidence_by_match_quality(self, pattern: FieldPattern, match: re.Match, text_content: str) -> float:
        """Adjust confidence based on match quality."""
        
        confidence = pattern.confidence_threshold
        extracted_value = match.group(1) if match.groups() else match.group(0)
        
        # Check value quality based on field type
        if pattern.field_type.value == "amount":
            # Good amount format increases confidence
            if re.match(r'^\d+[.,]\d{2}$', extracted_value):
                confidence += 0.2
            elif re.search(r'\d', extracted_value):
                confidence += 0.1
        
        elif pattern.field_type.value == "date":
            # Good date format increases confidence
            if re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', extracted_value):
                confidence += 0.2
            elif re.search(r'\d{2,4}', extracted_value):
                confidence += 0.1
        
        elif pattern.field_type.value == "vat_number":
            # Proper VAT format is crucial
            if re.match(r'^[A-Z]{2}\d{9}B\d{2}$', extracted_value):
                confidence += 0.3
            else:
                confidence -= 0.2
        
        elif pattern.field_type.value == "text":
            # Reasonable text length and content
            if 3 <= len(extracted_value) <= 100:
                confidence += 0.1
            if not extracted_value.isdigit():  # Not just numbers
                confidence += 0.1
        
        # Check for multiple matches (could indicate ambiguity)
        all_matches = re.findall(pattern.pattern, text_content, re.IGNORECASE | re.MULTILINE)
        if len(all_matches) > 1:
            confidence -= 0.1  # Slightly reduce confidence for ambiguous patterns
        
        return confidence
    
    def _adjust_confidence_by_specificity(self, pattern: FieldPattern, confidence: float) -> float:
        """Adjust confidence based on pattern specificity."""
        
        pattern_text = pattern.pattern
        
        # More specific patterns get higher confidence
        specificity_indicators = [
            (r'\\b', 0.1),  # Word boundaries
            (r'\[\^\s\]', 0.1),  # Character classes
            (r'\{.*\}', 0.1),  # Quantifiers
            (r'\(\?\:', 0.05),  # Non-capturing groups
            (r'[\[\(].*[\]\)]', 0.05),  # Groups/character sets
        ]
        
        for indicator, bonus in specificity_indicators:
            if re.search(indicator, pattern_text):
                confidence += bonus
        
        # Very short patterns are less reliable
        if len(pattern_text) < 10:
            confidence -= 0.1
        
        # Very long patterns might be over-fitted
        if len(pattern_text) > 100:
            confidence -= 0.05
        
        return confidence
    
    def _adjust_confidence_by_context(self, pattern: FieldPattern, match: re.Match, text_content: str) -> float:
        """Adjust confidence based on context around the match."""
        
        confidence = pattern.confidence_threshold
        
        # Get context around the match
        start, end = match.span()
        before_context = text_content[max(0, start-100):start].lower()
        after_context = text_content[end:end+100].lower()
        
        # Define expected context keywords for different field types
        context_keywords = {
            "amount": ["totaal", "total", "bedrag", "amount", "€", "eur", "betalen", "pay"],
            "date": ["datum", "date", "factuurdatum", "invoice date"],
            "invoice_number": ["factuur", "invoice", "nummer", "number", "nr"],
            "vat_number": ["btw", "vat", "belasting", "tax"],
            "supplier_name": ["leverancier", "supplier", "van", "from", "factuur van"]
        }
        
        field_type = pattern.field_type.value
        if field_type in context_keywords:
            keywords = context_keywords[field_type]
            
            # Check for positive context
            positive_context = any(keyword in before_context or keyword in after_context 
                                 for keyword in keywords)
            
            if positive_context:
                confidence += 0.15
        
        # Check for negative context (indicators that this might be wrong field)
        negative_keywords = {
            "amount": ["klantnummer", "customer", "telefoon", "phone", "email"],
            "date": ["bedrag", "amount", "€", "eur"],
            "invoice_number": ["datum", "date", "€", "eur", "btw"],
            "vat_number": ["datum", "date", "€", "eur", "factuur"],
            "supplier_name": ["€", "eur", "datum", "date", "btw"]
        }
        
        if field_type in negative_keywords:
            neg_keywords = negative_keywords[field_type]
            negative_context = any(keyword in before_context or keyword in after_context 
                                 for keyword in neg_keywords)
            
            if negative_context:
                confidence -= 0.1
        
        return confidence
    
    def _calculate_overall_confidence(self, field_confidences: Dict[str, float], template: Template) -> float:
        """Calculate overall confidence score."""
        
        if not field_confidences:
            return 0.0
        
        # Weight confidences by field importance
        weighted_sum = 0.0
        total_weight = 0.0
        
        for field_name, confidence in field_confidences.items():
            importance = self.field_importance.get(field_name, 0.01)  # Default low importance
            weighted_sum += confidence * importance
            total_weight += importance
        
        # Add bonus for required fields
        required_fields_found = 0
        required_fields_total = 0
        
        for rule in template.extraction_rules:
            if rule.required:
                required_fields_total += 1
                if rule.field_name in field_confidences and field_confidences[rule.field_name] > 0.5:
                    required_fields_found += 1
        
        required_field_bonus = 0.0
        if required_fields_total > 0:
            required_field_bonus = (required_fields_found / required_fields_total) * 0.2
        
        # Calculate base confidence
        base_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Apply required field bonus
        overall_confidence = min(base_confidence + required_field_bonus, 1.0)
        
        return overall_confidence
    
    def _calculate_quality_score(self, template: Template, text_content: str, field_confidences: Dict[str, float]) -> float:
        """Calculate overall quality score for the extraction."""
        
        scores = {}
        
        # Pattern specificity score
        scores["pattern_specificity"] = self._score_pattern_specificity(template)
        
        # Pattern coverage score
        scores["pattern_coverage"] = self._score_pattern_coverage(template, text_content)
        
        # Field completeness score
        scores["field_completeness"] = self._score_field_completeness(template, field_confidences)
        
        # Text quality score
        scores["text_quality"] = self._score_text_quality(text_content)
        
        # Template maturity score
        scores["template_maturity"] = self._score_template_maturity(template)
        
        # Calculate weighted average
        quality_score = sum(score * self.quality_weights[component] 
                          for component, score in scores.items())
        
        return min(quality_score, 1.0)
    
    def _score_pattern_specificity(self, template: Template) -> float:
        """Score pattern specificity."""
        
        if not template.extraction_rules:
            return 0.0
        
        specificity_scores = []
        
        for rule in template.extraction_rules:
            for pattern in rule.patterns:
                # Score based on pattern complexity
                pattern_text = pattern.pattern
                
                score = 0.5  # Base score
                
                # Bonus for specific constructs
                if re.search(r'\\b', pattern_text):
                    score += 0.1
                if re.search(r'\[.*\]', pattern_text):
                    score += 0.1
                if re.search(r'\{.*\}', pattern_text):
                    score += 0.1
                if len(pattern_text) > 20:
                    score += 0.1
                if pattern.validation_pattern:
                    score += 0.2
                
                specificity_scores.append(min(score, 1.0))
        
        return statistics.mean(specificity_scores) if specificity_scores else 0.0
    
    def _score_pattern_coverage(self, template: Template, text_content: str) -> float:
        """Score how well patterns cover the text content."""
        
        if not template.extraction_rules:
            return 0.0
        
        successful_patterns = 0
        total_patterns = 0
        
        for rule in template.extraction_rules:
            for pattern in rule.patterns:
                total_patterns += 1
                try:
                    if re.search(pattern.pattern, text_content, re.IGNORECASE | re.MULTILINE):
                        successful_patterns += 1
                except re.error:
                    pass
        
        return successful_patterns / total_patterns if total_patterns > 0 else 0.0
    
    def _score_field_completeness(self, template: Template, field_confidences: Dict[str, float]) -> float:
        """Score field completeness."""
        
        if not template.extraction_rules:
            return 0.0
        
        # Required fields
        required_fields = [rule.field_name for rule in template.extraction_rules if rule.required]
        total_fields = [rule.field_name for rule in template.extraction_rules]
        
        # Score required fields more heavily
        required_score = 0.0
        if required_fields:
            found_required = sum(1 for field in required_fields 
                               if field in field_confidences and field_confidences[field] > 0.5)
            required_score = found_required / len(required_fields)
        
        # Score all fields
        total_score = 0.0
        if total_fields:
            found_total = sum(1 for field in total_fields 
                            if field in field_confidences and field_confidences[field] > 0.3)
            total_score = found_total / len(total_fields)
        
        # Weighted combination
        return (required_score * 0.7) + (total_score * 0.3)
    
    def _score_text_quality(self, text_content: str) -> float:
        """Score text content quality."""
        
        score = 0.5  # Base score
        
        # Length check
        text_length = len(text_content)
        if text_length > 500:
            score += 0.2
        elif text_length > 200:
            score += 0.1
        
        # Structure indicators
        if re.search(r'factuur|invoice', text_content, re.IGNORECASE):
            score += 0.1
        if re.search(r'€|\d+[.,]\d{2}', text_content):
            score += 0.1
        if re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text_content):
            score += 0.1
        
        # OCR quality indicators
        ocr_errors = len(re.findall(r'[^\w\s€\.,\-/()]+', text_content))
        if ocr_errors < text_length * 0.01:  # Less than 1% unusual characters
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_template_maturity(self, template: Template) -> float:
        """Score template maturity based on usage and success rate."""
        
        score = 0.5  # Base score for new templates
        
        # Usage count bonus
        if hasattr(template, 'usage_count'):
            if template.usage_count > 50:
                score += 0.3
            elif template.usage_count > 10:
                score += 0.2
            elif template.usage_count > 0:
                score += 0.1
        
        # Success rate bonus
        if hasattr(template, 'success_rate'):
            if template.success_rate > 0.9:
                score += 0.2
            elif template.success_rate > 0.7:
                score += 0.1
        
        return min(score, 1.0)
    
    def _generate_recommendations(self, template: Template, text_content: str, 
                                field_confidences: Dict[str, float], quality_score: float) -> List[str]:
        """Generate recommendations for improving extraction confidence."""
        
        recommendations = []
        
        # Overall quality recommendations
        if quality_score < 0.5:
            recommendations.append("Overall quality is low. Consider improving template patterns or using higher quality PDFs.")
        elif quality_score < 0.7:
            recommendations.append("Overall quality is moderate. Some improvements may be beneficial.")
        
        # Field-specific recommendations
        low_confidence_fields = [field for field, conf in field_confidences.items() if conf < 0.5]
        
        if low_confidence_fields:
            recommendations.append(f"Low confidence fields detected: {', '.join(low_confidence_fields)}. "
                                 "Consider reviewing and improving patterns for these fields.")
        
        # Required field recommendations
        required_fields = [rule.field_name for rule in template.extraction_rules if rule.required]
        missing_required = [field for field in required_fields 
                          if field not in field_confidences or field_confidences[field] < 0.5]
        
        if missing_required:
            recommendations.append(f"Required fields with low confidence: {', '.join(missing_required)}. "
                                 "These fields are critical for successful extraction.")
        
        # Pattern-specific recommendations
        if not any(re.search(r'factuur|invoice', text_content, re.IGNORECASE)):
            recommendations.append("Document doesn't appear to be an invoice. Verify document type.")
        
        # Template improvement recommendations
        if hasattr(template, 'usage_count') and template.usage_count < 5:
            recommendations.append("Template has limited usage history. More testing with sample documents is recommended.")
        
        # Text quality recommendations
        if len(text_content) < 200:
            recommendations.append("Text content is very short. This may indicate OCR issues or incomplete extraction.")
        
        if not recommendations:
            recommendations.append("Extraction confidence looks good. No specific improvements needed.")
        
        return recommendations