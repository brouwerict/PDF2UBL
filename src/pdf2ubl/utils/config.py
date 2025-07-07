"""Configuration management for PDF2UBL."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from decouple import config


@dataclass
class Config:
    """Configuration settings for PDF2UBL."""
    
    # General settings
    debug: bool = False
    log_level: str = "INFO"
    log_file: str = "pdf2ubl.log"
    
    # Templates
    templates_dir: str = "templates"
    auto_create_templates: bool = True
    
    # PDF Processing
    use_ocr: bool = False
    ocr_language: str = "nld"
    pdf_timeout: int = 30
    
    # UBL Export
    default_currency: str = "EUR"
    default_country: str = "NL"
    default_vat_rate: float = 21.0
    ubl_validation: bool = True
    
    # Template Engine
    min_confidence: float = 0.3
    strict_mode: bool = False
    fallback_enabled: bool = True
    
    # Performance
    max_file_size_mb: int = 50
    max_concurrent_files: int = 4
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    
    # API Settings (for future web interface)
    api_host: str = "localhost"
    api_port: int = 8000
    api_cors_origins: list = field(default_factory=lambda: ["*"])
    
    # Database (for future use)
    database_url: Optional[str] = None
    
    # Security
    max_upload_size_mb: int = 10
    allowed_file_types: list = field(default_factory=lambda: ["pdf"])
    
    @classmethod
    def load_from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        
        return cls(
            debug=config('PDF2UBL_DEBUG', default=False, cast=bool),
            log_level=config('PDF2UBL_LOG_LEVEL', default='INFO'),
            log_file=config('PDF2UBL_LOG_FILE', default='pdf2ubl.log'),
            
            templates_dir=config('PDF2UBL_TEMPLATES_DIR', default='templates'),
            auto_create_templates=config('PDF2UBL_AUTO_CREATE_TEMPLATES', default=True, cast=bool),
            
            use_ocr=config('PDF2UBL_USE_OCR', default=False, cast=bool),
            ocr_language=config('PDF2UBL_OCR_LANGUAGE', default='nld'),
            pdf_timeout=config('PDF2UBL_PDF_TIMEOUT', default=30, cast=int),
            
            default_currency=config('PDF2UBL_DEFAULT_CURRENCY', default='EUR'),
            default_country=config('PDF2UBL_DEFAULT_COUNTRY', default='NL'),
            default_vat_rate=config('PDF2UBL_DEFAULT_VAT_RATE', default=21.0, cast=float),
            ubl_validation=config('PDF2UBL_UBL_VALIDATION', default=True, cast=bool),
            
            min_confidence=config('PDF2UBL_MIN_CONFIDENCE', default=0.3, cast=float),
            strict_mode=config('PDF2UBL_STRICT_MODE', default=False, cast=bool),
            fallback_enabled=config('PDF2UBL_FALLBACK_ENABLED', default=True, cast=bool),
            
            max_file_size_mb=config('PDF2UBL_MAX_FILE_SIZE_MB', default=50, cast=int),
            max_concurrent_files=config('PDF2UBL_MAX_CONCURRENT_FILES', default=4, cast=int),
            cache_enabled=config('PDF2UBL_CACHE_ENABLED', default=True, cast=bool),
            cache_ttl_hours=config('PDF2UBL_CACHE_TTL_HOURS', default=24, cast=int),
            
            api_host=config('PDF2UBL_API_HOST', default='localhost'),
            api_port=config('PDF2UBL_API_PORT', default=8000, cast=int),
            
            database_url=config('PDF2UBL_DATABASE_URL', default=None),
            
            max_upload_size_mb=config('PDF2UBL_MAX_UPLOAD_SIZE_MB', default=10, cast=int),
        )
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'Config':
        """Load configuration from JSON file."""
        
        if not config_path.exists():
            return cls()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return cls(**config_data)
    
    def save_to_file(self, config_path: Path):
        """Save configuration to JSON file."""
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_data = {
            'debug': self.debug,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'templates_dir': self.templates_dir,
            'auto_create_templates': self.auto_create_templates,
            'use_ocr': self.use_ocr,
            'ocr_language': self.ocr_language,
            'pdf_timeout': self.pdf_timeout,
            'default_currency': self.default_currency,
            'default_country': self.default_country,
            'default_vat_rate': self.default_vat_rate,
            'ubl_validation': self.ubl_validation,
            'min_confidence': self.min_confidence,
            'strict_mode': self.strict_mode,
            'fallback_enabled': self.fallback_enabled,
            'max_file_size_mb': self.max_file_size_mb,
            'max_concurrent_files': self.max_concurrent_files,
            'cache_enabled': self.cache_enabled,
            'cache_ttl_hours': self.cache_ttl_hours,
            'api_host': self.api_host,
            'api_port': self.api_port,
            'api_cors_origins': self.api_cors_origins,
            'database_url': self.database_url,
            'max_upload_size_mb': self.max_upload_size_mb,
            'allowed_file_types': self.allowed_file_types
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def update_from_dict(self, updates: Dict[str, Any]):
        """Update configuration from dictionary."""
        
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        
        return {
            'debug': self.debug,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'templates_dir': self.templates_dir,
            'auto_create_templates': self.auto_create_templates,
            'use_ocr': self.use_ocr,
            'ocr_language': self.ocr_language,
            'pdf_timeout': self.pdf_timeout,
            'default_currency': self.default_currency,
            'default_country': self.default_country,
            'default_vat_rate': self.default_vat_rate,
            'ubl_validation': self.ubl_validation,
            'min_confidence': self.min_confidence,
            'strict_mode': self.strict_mode,
            'fallback_enabled': self.fallback_enabled,
            'max_file_size_mb': self.max_file_size_mb,
            'max_concurrent_files': self.max_concurrent_files,
            'cache_enabled': self.cache_enabled,
            'cache_ttl_hours': self.cache_ttl_hours,
            'api_host': self.api_host,
            'api_port': self.api_port,
            'api_cors_origins': self.api_cors_origins,
            'database_url': self.database_url,
            'max_upload_size_mb': self.max_upload_size_mb,
            'allowed_file_types': self.allowed_file_types
        }


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file or environment.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Config object
    """
    
    # Default config file paths
    default_paths = [
        Path('pdf2ubl.json'),
        Path('config/pdf2ubl.json'),
        Path.home() / '.pdf2ubl' / 'config.json',
        Path('/etc/pdf2ubl/config.json')
    ]
    
    # Use provided path or find existing config file
    if config_path:
        config_paths = [config_path]
    else:
        config_paths = [path for path in default_paths if path.exists()]
    
    # Load from file if available, otherwise from environment
    if config_paths:
        config = Config.load_from_file(config_paths[0])
    else:
        config = Config.load_from_env()
    
    # Override with environment variables if they exist
    env_config = Config.load_from_env()
    
    # Only override non-default values
    if config != Config():  # If config was loaded from file
        for attr in dir(env_config):
            if not attr.startswith('_'):
                env_value = getattr(env_config, attr)
                default_value = getattr(Config(), attr)
                
                # Only use env value if it's different from default
                if env_value != default_value:
                    setattr(config, attr, env_value)
    
    return config


def create_default_config(config_path: Path):
    """Create a default configuration file."""
    
    config = Config()
    config.save_to_file(config_path)
    
    return config


def get_config_paths() -> list[Path]:
    """Get list of possible configuration file paths."""
    
    return [
        Path('pdf2ubl.json'),
        Path('config/pdf2ubl.json'),
        Path.home() / '.pdf2ubl' / 'config.json',
        Path('/etc/pdf2ubl/config.json')
    ]