"""Template models for supplier-specific extraction patterns."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum


class FieldType(Enum):
    """Types of fields that can be extracted."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    AMOUNT = "amount"
    PERCENTAGE = "percentage"
    VAT_NUMBER = "vat_number"
    IBAN = "iban"
    EMAIL = "email"
    PHONE = "phone"


class ExtractionMethod(Enum):
    """Methods for extracting field values."""
    REGEX = "regex"
    POSITION = "position"
    KEYWORD = "keyword"
    TABLE = "table"
    ML_MODEL = "ml_model"


@dataclass
class FieldPattern:
    """Pattern for extracting a specific field."""
    
    # Pattern definition
    pattern: str
    method: ExtractionMethod
    field_type: FieldType
    
    # Pattern options
    case_sensitive: bool = False
    multiline: bool = False
    whole_word: bool = False
    
    # Confidence and validation
    confidence_threshold: float = 0.5
    validation_pattern: Optional[str] = None
    
    # Position constraints (for position-based extraction)
    min_x: Optional[float] = None
    max_x: Optional[float] = None
    min_y: Optional[float] = None
    max_y: Optional[float] = None
    
    # Context requirements
    required_context: List[str] = field(default_factory=list)
    forbidden_context: List[str] = field(default_factory=list)
    
    # Post-processing
    cleanup_pattern: Optional[str] = None
    replacement_pattern: Optional[str] = None
    
    # Metadata
    name: Optional[str] = None
    description: Optional[str] = None
    priority: int = 0


@dataclass
class ExtractionRule:
    """Rule for extracting a field with multiple patterns."""
    
    field_name: str
    field_type: FieldType
    patterns: List[FieldPattern]
    
    # Combination logic
    use_best_match: bool = True  # Use pattern with highest confidence
    require_all: bool = False    # Require all patterns to match
    
    # Validation
    required: bool = False
    min_confidence: float = 0.3
    
    # Default values
    default_value: Optional[Any] = None
    fallback_patterns: List[FieldPattern] = field(default_factory=list)


@dataclass
class TableExtractionRule:
    """Rule for extracting data from tables."""
    
    table_name: str
    
    # Table identification
    header_patterns: List[str] = field(default_factory=list)
    position_hints: Dict[str, Any] = field(default_factory=dict)
    
    # Column mapping
    column_mapping: Dict[str, str] = field(default_factory=dict)
    
    # Row processing
    skip_rows: int = 0
    max_rows: Optional[int] = None
    row_filter_pattern: Optional[str] = None
    
    # Data processing
    numeric_columns: List[str] = field(default_factory=list)
    date_columns: List[str] = field(default_factory=list)
    
    # Validation
    required_columns: List[str] = field(default_factory=list)
    min_rows: int = 0


@dataclass
class Template:
    """Complete template for supplier-specific extraction."""
    
    # Template metadata
    template_id: str
    name: str
    description: str = ""
    version: str = "1.0"
    
    # Supplier identification
    supplier_patterns: List[FieldPattern] = field(default_factory=list)
    supplier_name: Optional[str] = None
    supplier_aliases: List[str] = field(default_factory=list)
    
    # Field extraction rules
    extraction_rules: List[ExtractionRule] = field(default_factory=list)
    
    # Table extraction rules
    table_rules: List[TableExtractionRule] = field(default_factory=list)
    
    # Template configuration
    language: str = "nl"
    currency: str = "EUR"
    date_format: str = "%d-%m-%Y"
    decimal_separator: str = ","
    thousands_separator: str = "."
    
    # Processing options
    ocr_enabled: bool = False
    ml_enabled: bool = False
    fallback_enabled: bool = True
    
    # Validation settings
    strict_mode: bool = False
    min_confidence: float = 0.3
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    usage_count: int = 0
    success_rate: float = 0.0
    
    # Training data
    training_samples: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_field_rule(self, 
                      field_name: str, 
                      field_type: FieldType,
                      patterns: List[FieldPattern],
                      required: bool = False,
                      min_confidence: float = 0.3) -> ExtractionRule:
        """Add a field extraction rule."""
        
        rule = ExtractionRule(
            field_name=field_name,
            field_type=field_type,
            patterns=patterns,
            required=required,
            min_confidence=min_confidence
        )
        
        self.extraction_rules.append(rule)
        return rule
    
    def add_table_rule(self,
                      table_name: str,
                      header_patterns: List[str],
                      column_mapping: Dict[str, str],
                      required_columns: List[str] = None) -> TableExtractionRule:
        """Add a table extraction rule."""
        
        rule = TableExtractionRule(
            table_name=table_name,
            header_patterns=header_patterns,
            column_mapping=column_mapping,
            required_columns=required_columns or []
        )
        
        self.table_rules.append(rule)
        return rule
    
    def get_rule_by_field(self, field_name: str) -> Optional[ExtractionRule]:
        """Get extraction rule by field name."""
        
        for rule in self.extraction_rules:
            if rule.field_name == field_name:
                return rule
        
        return None
    
    def get_table_rule_by_name(self, table_name: str) -> Optional[TableExtractionRule]:
        """Get table extraction rule by name."""
        
        for rule in self.table_rules:
            if rule.table_name == table_name:
                return rule
        
        return None
    
    def update_success_rate(self, success: bool):
        """Update template success rate."""
        
        self.usage_count += 1
        
        if success:
            # Calculate new success rate
            current_successes = self.success_rate * (self.usage_count - 1)
            new_successes = current_successes + 1
            self.success_rate = new_successes / self.usage_count
        else:
            # Recalculate success rate
            current_successes = self.success_rate * (self.usage_count - 1)
            self.success_rate = current_successes / self.usage_count
        
        self.updated_date = datetime.now()
    
    def add_training_sample(self, pdf_path: str, extracted_data: Dict[str, Any]):
        """Add training sample for ML improvement."""
        
        sample = {
            'pdf_path': pdf_path,
            'extracted_data': extracted_data,
            'timestamp': datetime.now().isoformat(),
            'template_version': self.version
        }
        
        self.training_samples.append(sample)
        
        # Limit training samples to prevent memory issues
        if len(self.training_samples) > 100:
            self.training_samples = self.training_samples[-100:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for serialization."""
        
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'supplier_patterns': [
                {
                    'pattern': p.pattern,
                    'method': p.method.value,
                    'field_type': p.field_type.value,
                    'case_sensitive': p.case_sensitive,
                    'confidence_threshold': p.confidence_threshold,
                    'name': p.name,
                    'description': p.description,
                    'priority': p.priority
                }
                for p in self.supplier_patterns
            ],
            'supplier_name': self.supplier_name,
            'supplier_aliases': self.supplier_aliases,
            'extraction_rules': [
                {
                    'field_name': r.field_name,
                    'field_type': r.field_type.value,
                    'patterns': [
                        {
                            'pattern': p.pattern,
                            'method': p.method.value,
                            'field_type': p.field_type.value,
                            'case_sensitive': p.case_sensitive,
                            'confidence_threshold': p.confidence_threshold,
                            'validation_pattern': p.validation_pattern,
                            'name': p.name,
                            'description': p.description,
                            'priority': p.priority
                        }
                        for p in r.patterns
                    ],
                    'required': r.required,
                    'min_confidence': r.min_confidence,
                    'default_value': r.default_value
                }
                for r in self.extraction_rules
            ],
            'table_rules': [
                {
                    'table_name': t.table_name,
                    'header_patterns': t.header_patterns,
                    'column_mapping': t.column_mapping,
                    'required_columns': t.required_columns,
                    'min_rows': t.min_rows
                }
                for t in self.table_rules
            ],
            'language': self.language,
            'currency': self.currency,
            'date_format': self.date_format,
            'decimal_separator': self.decimal_separator,
            'thousands_separator': self.thousands_separator,
            'ocr_enabled': self.ocr_enabled,
            'ml_enabled': self.ml_enabled,
            'fallback_enabled': self.fallback_enabled,
            'strict_mode': self.strict_mode,
            'min_confidence': self.min_confidence,
            'created_date': self.created_date.isoformat(),
            'updated_date': self.updated_date.isoformat(),
            'created_by': self.created_by,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """Create template from dictionary."""
        
        template = cls(
            template_id=data['template_id'],
            name=data['name'],
            description=data.get('description', ''),
            version=data.get('version', '1.0'),
            supplier_name=data.get('supplier_name'),
            supplier_aliases=data.get('supplier_aliases', []),
            language=data.get('language', 'nl'),
            currency=data.get('currency', 'EUR'),
            date_format=data.get('date_format', '%d-%m-%Y'),
            decimal_separator=data.get('decimal_separator', ','),
            thousands_separator=data.get('thousands_separator', '.'),
            ocr_enabled=data.get('ocr_enabled', False),
            ml_enabled=data.get('ml_enabled', False),
            fallback_enabled=data.get('fallback_enabled', True),
            strict_mode=data.get('strict_mode', False),
            min_confidence=data.get('min_confidence', 0.3),
            created_by=data.get('created_by', 'system'),
            usage_count=data.get('usage_count', 0),
            success_rate=data.get('success_rate', 0.0)
        )
        
        # Parse dates
        if 'created_date' in data:
            template.created_date = datetime.fromisoformat(data['created_date'])
        if 'updated_date' in data:
            template.updated_date = datetime.fromisoformat(data['updated_date'])
        
        # Parse supplier patterns
        if 'supplier_patterns' in data:
            for p_data in data['supplier_patterns']:
                pattern = FieldPattern(
                    pattern=p_data['pattern'],
                    method=ExtractionMethod(p_data['method']),
                    field_type=FieldType(p_data['field_type']),
                    case_sensitive=p_data.get('case_sensitive', False),
                    confidence_threshold=p_data.get('confidence_threshold', 0.5),
                    validation_pattern=p_data.get('validation_pattern'),
                    name=p_data.get('name'),
                    description=p_data.get('description'),
                    priority=p_data.get('priority', 0)
                )
                template.supplier_patterns.append(pattern)
        
        # Parse extraction rules
        if 'extraction_rules' in data:
            for r_data in data['extraction_rules']:
                patterns = []
                for p_data in r_data['patterns']:
                    pattern = FieldPattern(
                        pattern=p_data['pattern'],
                        method=ExtractionMethod(p_data['method']),
                        field_type=FieldType(p_data['field_type']),
                        case_sensitive=p_data.get('case_sensitive', False),
                        confidence_threshold=p_data.get('confidence_threshold', 0.5),
                        validation_pattern=p_data.get('validation_pattern'),
                        name=p_data.get('name'),
                        description=p_data.get('description'),
                        priority=p_data.get('priority', 0)
                    )
                    patterns.append(pattern)
                
                rule = ExtractionRule(
                    field_name=r_data['field_name'],
                    field_type=FieldType(r_data['field_type']),
                    patterns=patterns,
                    required=r_data.get('required', False),
                    min_confidence=r_data.get('min_confidence', 0.3),
                    default_value=r_data.get('default_value')
                )
                template.extraction_rules.append(rule)
        
        # Parse table rules
        if 'table_rules' in data:
            for t_data in data['table_rules']:
                rule = TableExtractionRule(
                    table_name=t_data['table_name'],
                    header_patterns=t_data.get('header_patterns', []),
                    column_mapping=t_data.get('column_mapping', {}),
                    required_columns=t_data.get('required_columns', []),
                    min_rows=t_data.get('min_rows', 0)
                )
                template.table_rules.append(rule)
        
        return template