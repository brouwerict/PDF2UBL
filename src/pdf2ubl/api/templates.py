"""Templates API router for PDF2UBL GUI."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from ..templates.template_manager import TemplateManager
from ..templates.template_models import Template, FieldType, ExtractionMethod

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for API
class TemplateResponse(BaseModel):
    """Response model for template data."""
    template_id: str
    name: str
    supplier_name: Optional[str] = None
    description: Optional[str] = None
    supplier_aliases: List[str] = []
    usage_count: int = 0
    success_rate: float = 0.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class TemplateCreate(BaseModel):
    """Model for creating a new template."""
    template_id: str
    name: str
    supplier_name: Optional[str] = None
    description: Optional[str] = None

class TemplateUpdate(BaseModel):
    """Model for updating an existing template."""
    name: Optional[str] = None
    supplier_name: Optional[str] = None
    description: Optional[str] = None

class PatternCreate(BaseModel):
    """Model for creating extraction patterns."""
    pattern: str
    method: str  # Will be converted to ExtractionMethod enum
    field_type: str  # Will be converted to FieldType enum
    confidence_threshold: float = 0.5
    name: Optional[str] = None
    description: Optional[str] = None

class FieldRuleCreate(BaseModel):
    """Model for creating field extraction rules."""
    field_name: str
    field_type: str
    patterns: List[PatternCreate]
    required: bool = False
    min_confidence: float = 0.3

# Dependency to get template manager
def get_template_manager():
    """Get template manager instance."""
    return TemplateManager()

@router.get("/", response_model=List[TemplateResponse])
async def list_templates(template_manager: TemplateManager = Depends(get_template_manager)):
    """List all available templates."""
    try:
        templates = template_manager.get_templates()
        return [
            TemplateResponse(
                template_id=template.template_id,
                name=template.name,
                supplier_name=template.supplier_name,
                description=template.description,
                supplier_aliases=template.supplier_aliases,
                usage_count=template.usage_count,
                success_rate=template.success_rate,
                created_at=template.created_date.isoformat() if template.created_date else None,
                updated_at=template.updated_date.isoformat() if template.updated_date else None
            )
            for template in templates
        ]
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, template_manager: TemplateManager = Depends(get_template_manager)):
    """Get a specific template by ID."""
    try:
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return TemplateResponse(
            template_id=template.template_id,
            name=template.name,
            supplier_name=template.supplier_name,
            description=template.description,
            supplier_aliases=template.supplier_aliases,
            usage_count=template.usage_count,
            success_rate=template.success_rate,
            created_at=template.created_date.isoformat() if template.created_date else None,
            updated_at=template.updated_date.isoformat() if template.updated_date else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template")

@router.post("/", response_model=TemplateResponse)
async def create_template(template_data: TemplateCreate, template_manager: TemplateManager = Depends(get_template_manager)):
    """Create a new template."""
    try:
        # Check if template already exists
        if template_manager.get_template(template_data.template_id):
            raise HTTPException(status_code=400, detail="Template already exists")
        
        # Create new template
        template = template_manager.create_template(
            template_id=template_data.template_id,
            name=template_data.name,
            supplier_name=template_data.supplier_name,
            description=template_data.description or ""
        )
        
        # Save template
        template_manager.save_template(template)
        
        return TemplateResponse(
            template_id=template.template_id,
            name=template.name,
            supplier_name=template.supplier_name,
            description=template.description,
            supplier_aliases=template.supplier_aliases,
            usage_count=template.usage_count,
            success_rate=template.success_rate,
            created_at=template.created_date.isoformat() if template.created_date else None,
            updated_at=template.updated_date.isoformat() if template.updated_date else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template")

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: str, template_data: TemplateUpdate, template_manager: TemplateManager = Depends(get_template_manager)):
    """Update an existing template."""
    try:
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Update template fields
        if template_data.name is not None:
            template.name = template_data.name
        if template_data.supplier_name is not None:
            template.supplier_name = template_data.supplier_name
        if template_data.description is not None:
            template.description = template_data.description
        
        # Save updated template
        template_manager.save_template(template)
        
        return TemplateResponse(
            template_id=template.template_id,
            name=template.name,
            supplier_name=template.supplier_name,
            description=template.description,
            supplier_aliases=template.supplier_aliases,
            usage_count=template.usage_count,
            success_rate=template.success_rate,
            created_at=template.created_date.isoformat() if template.created_date else None,
            updated_at=template.updated_date.isoformat() if template.updated_date else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update template")

@router.delete("/{template_id}")
async def delete_template(template_id: str, template_manager: TemplateManager = Depends(get_template_manager)):
    """Delete a template."""
    try:
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template_manager.delete_template(template_id)
        return {"message": "Template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete template")

@router.get("/{template_id}/details")
async def get_template_details(template_id: str, template_manager: TemplateManager = Depends(get_template_manager)):
    """Get detailed template information including rules and patterns."""
    try:
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Convert template to detailed dict
        return {
            "template_id": template.template_id,
            "name": template.name,
            "supplier_name": template.supplier_name,
            "description": template.description,
            "supplier_aliases": template.supplier_aliases,
            "supplier_patterns": [
                {
                    "pattern": pattern.pattern,
                    "method": pattern.method.value,
                    "field_type": pattern.field_type.value,
                    "confidence_threshold": pattern.confidence_threshold,
                    "name": pattern.name,
                    "description": pattern.description
                }
                for pattern in template.supplier_patterns
            ],
            "extraction_rules": [
                {
                    "field_name": rule.field_name,
                    "field_type": rule.field_type.value,
                    "required": rule.required,
                    "min_confidence": rule.min_confidence,
                    "patterns": [
                        {
                            "pattern": pattern.pattern,
                            "method": pattern.method.value,
                            "field_type": pattern.field_type.value,
                            "confidence_threshold": pattern.confidence_threshold,
                            "name": pattern.name,
                            "description": pattern.description
                        }
                        for pattern in rule.patterns
                    ]
                }
                for rule in template.extraction_rules
            ],
            "usage_count": template.usage_count,
            "success_rate": template.success_rate,
            "created_at": template.created_date.isoformat() if template.created_date else None,
            "updated_at": template.updated_date.isoformat() if template.updated_date else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template details {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template details")

@router.post("/{template_id}/rules")
async def add_field_rule(template_id: str, rule_data: FieldRuleCreate, template_manager: TemplateManager = Depends(get_template_manager)):
    """Add a field extraction rule to a template."""
    try:
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Convert string enums to actual enums
        try:
            field_type = FieldType(rule_data.field_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid field type: {rule_data.field_type}")
        
        # Convert patterns
        patterns = []
        for pattern_data in rule_data.patterns:
            try:
                method = ExtractionMethod(pattern_data.method)
                pattern_field_type = FieldType(pattern_data.field_type)
                
                from ..templates.template_models import FieldPattern
                pattern = FieldPattern(
                    pattern=pattern_data.pattern,
                    method=method,
                    field_type=pattern_field_type,
                    confidence_threshold=pattern_data.confidence_threshold,
                    name=pattern_data.name,
                    description=pattern_data.description
                )
                patterns.append(pattern)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid pattern data: {str(e)}")
        
        # Add rule to template
        template.add_field_rule(
            field_name=rule_data.field_name,
            field_type=field_type,
            patterns=patterns,
            required=rule_data.required,
            min_confidence=rule_data.min_confidence
        )
        
        # Save updated template
        template_manager.save_template(template)
        
        return {"message": "Field rule added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding field rule to template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add field rule")

@router.get("/stats/overview")
async def get_template_stats(template_manager: TemplateManager = Depends(get_template_manager)):
    """Get template statistics overview."""
    try:
        stats = template_manager.get_template_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting template statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template statistics")

@router.post("/import")
async def import_templates(file_path: str, template_manager: TemplateManager = Depends(get_template_manager)):
    """Import templates from a file."""
    try:
        # Sanitize and validate file path to prevent path traversal
        import_path = Path(file_path).resolve()
        
        # Ensure the path is within allowed directories (security check)
        allowed_dirs = [Path("templates").resolve(), Path("imports").resolve()]
        if not any(str(import_path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
            raise HTTPException(status_code=403, detail="File path not allowed")
        
        if not import_path.exists():
            raise HTTPException(status_code=404, detail="Import file not found")
        
        imported_count = template_manager.import_templates(import_path)
        return {"message": f"Successfully imported {imported_count} templates"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to import templates")

@router.post("/export")
async def export_templates(output_path: str, template_manager: TemplateManager = Depends(get_template_manager)):
    """Export all templates to a file."""
    try:
        export_path = Path(output_path)
        template_manager.export_templates(export_path)
        return {"message": f"Successfully exported templates to {output_path}"}
    except Exception as e:
        logger.error(f"Error exporting templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to export templates")