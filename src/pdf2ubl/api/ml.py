"""Machine Learning API router for PDF2UBL GUI."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import tempfile
import logging
import json
from datetime import datetime

from ..ml.template_generator import TemplateGenerator
from ..ml.pattern_analyzer import PatternAnalyzer
from ..ml.confidence_predictor import ConfidencePredictor
from ..extractors.pdf_extractor import PDFExtractor
from ..templates.template_manager import TemplateManager
from ..templates.template_engine import TemplateEngine

logger = logging.getLogger(__name__)

router = APIRouter()

def _safe_date_isoformat(date_value) -> Optional[str]:
    """Safely convert date to ISO format string."""
    if not date_value:
        return None
    
    # If already a datetime object, use isoformat
    if hasattr(date_value, 'isoformat'):
        return date_value.isoformat()
    
    # If it's a string, try to parse it first
    if isinstance(date_value, str):
        try:
            # Handle Dutch month names
            dutch_months = {
                'januari': 'January', 'februari': 'February', 'maart': 'March',
                'april': 'April', 'mei': 'May', 'juni': 'June',
                'juli': 'July', 'augustus': 'August', 'september': 'September',
                'oktober': 'October', 'november': 'November', 'december': 'December'
            }
            
            # Replace Dutch month names with English for parsing
            date_str_en = date_value
            for dutch, english in dutch_months.items():
                date_str_en = date_str_en.replace(dutch, english)
            
            # Try various date formats
            for fmt in ['%d %B %Y', '%d.%m.%Y', '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d']:
                try:
                    parsed_date = datetime.strptime(date_str_en, fmt)
                    return parsed_date.isoformat()
                except ValueError:
                    continue
            
            # If no format works, return the original string
            return date_value
        except:
            return str(date_value)
    
    # For any other type, convert to string
    return str(date_value)

# Pydantic models for ML API
class TemplateGenerationRequest(BaseModel):
    """Request model for auto-template generation."""
    supplier_name: str
    template_id: Optional[str] = None
    sample_pdfs: List[str] = []  # File paths to sample PDFs
    confidence_threshold: float = 0.5

class TemplateGenerationResponse(BaseModel):
    """Response model for template generation."""
    template_id: str
    template_name: str
    confidence_score: float
    suggested_patterns: List[Dict[str, Any]]
    field_mappings: Dict[str, str]
    supplier_patterns: List[Dict[str, Any]]
    raw_text_preview: Optional[str] = None

class PatternAnalysisRequest(BaseModel):
    """Request model for pattern analysis."""
    text_samples: List[str]
    field_type: str
    existing_patterns: List[str] = []

class PatternAnalysisResponse(BaseModel):
    """Response model for pattern analysis."""
    suggested_patterns: List[Dict[str, Any]]
    confidence_scores: List[float]
    pattern_coverage: float
    recommendations: List[str]

class ConfidencePredictionRequest(BaseModel):
    """Request model for confidence prediction."""
    template_id: str
    text_content: str

class ConfidencePredictionResponse(BaseModel):
    """Response model for confidence prediction."""
    overall_confidence: float
    field_confidences: Dict[str, float]
    quality_score: float
    recommendations: List[str]

class TrainingRequest(BaseModel):
    """Request model for ML model training."""
    training_data_path: str
    model_type: str  # "template_generator", "pattern_analyzer", "confidence_predictor"
    hyperparameters: Dict[str, Any] = {}

class TrainingResponse(BaseModel):
    """Response model for training."""
    job_id: str
    model_type: str
    status: str
    training_metrics: Optional[Dict[str, float]] = None

# Dependencies
def get_template_generator():
    """Get template generator instance."""
    return TemplateGenerator()

def get_pattern_analyzer():
    """Get pattern analyzer instance."""
    return PatternAnalyzer()

def get_confidence_predictor():
    """Get confidence predictor instance."""
    return ConfidencePredictor()

def get_pdf_extractor():
    """Get PDF extractor instance."""
    return PDFExtractor()

def get_template_manager():
    """Get template manager instance."""
    return TemplateManager()

def get_template_engine():
    """Get template engine instance."""
    return TemplateEngine()

@router.post("/generate-template")
async def generate_template_from_files(
    supplier_name: str = Form(...),
    template_id: Optional[str] = Form(None),
    confidence_threshold: float = Form(0.5),
    files: List[UploadFile] = File(...),
    template_generator: TemplateGenerator = Depends(get_template_generator),
    template_manager: TemplateManager = Depends(get_template_manager)
):
    """Generate a new template using ML analysis of uploaded sample PDFs."""
    
    try:
        if not files:
            raise HTTPException(status_code=400, detail="At least one sample PDF is required")
        
        # Save uploaded files temporarily
        sample_paths = []
        temp_files = []
        
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"Only PDF files are supported: {file.filename}")
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                temp_files.append(tmp_file.name)
                sample_paths.append(Path(tmp_file.name))
        
        # Generate template ID if not provided
        template_id = template_id or f"{supplier_name.lower().replace(' ', '_')}_ml"
        
        # Check if template already exists
        if template_manager.get_template(template_id):
            raise HTTPException(status_code=400, detail=f"Template already exists: {template_id}")
        
        # Generate template using ML
        logger.info(f"Generating template for {supplier_name} with {len(sample_paths)} samples")
        
        generated_template = template_generator.generate_template(
            supplier_name=supplier_name,
            template_id=template_id,
            sample_pdfs=sample_paths,
            confidence_threshold=confidence_threshold
        )
        
        # Save generated template
        template_manager.save_template(generated_template.template)
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")
        
        return TemplateGenerationResponse(
            template_id=template_id,
            template_name=generated_template.template.name,
            confidence_score=generated_template.confidence_score,
            suggested_patterns=generated_template.suggested_patterns,
            field_mappings=generated_template.field_mappings,
            supplier_patterns=generated_template.supplier_patterns
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        # Clean up temporary files on error
        for temp_file in temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except:
                pass
        raise HTTPException(status_code=500, detail="Failed to generate template")

@router.post("/analyze-patterns", response_model=PatternAnalysisResponse)
async def analyze_patterns(
    request: PatternAnalysisRequest,
    pattern_analyzer: PatternAnalyzer = Depends(get_pattern_analyzer)
):
    """Analyze text samples to suggest extraction patterns."""
    
    try:
        if not request.text_samples:
            raise HTTPException(status_code=400, detail="At least one text sample is required")
        
        # Analyze patterns
        logger.info(f"Analyzing patterns for {len(request.text_samples)} text samples")
        
        analysis_result = pattern_analyzer.analyze_patterns(
            text_samples=request.text_samples,
            field_type=request.field_type,
            existing_patterns=request.existing_patterns
        )
        
        return PatternAnalysisResponse(
            suggested_patterns=analysis_result.suggested_patterns,
            confidence_scores=analysis_result.confidence_scores,
            pattern_coverage=analysis_result.pattern_coverage,
            recommendations=analysis_result.recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze patterns")

@router.post("/predict-confidence", response_model=ConfidencePredictionResponse)
async def predict_confidence(
    request: ConfidencePredictionRequest,
    confidence_predictor: ConfidencePredictor = Depends(get_confidence_predictor),
    template_manager: TemplateManager = Depends(get_template_manager)
):
    """Predict extraction confidence for given text and template."""
    
    try:
        # Get template
        template = template_manager.get_template(request.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Predict confidence
        logger.info(f"Predicting confidence for template {request.template_id}")
        
        prediction_result = confidence_predictor.predict_confidence(
            template=template,
            text_content=request.text_content
        )
        
        return ConfidencePredictionResponse(
            overall_confidence=prediction_result.overall_confidence,
            field_confidences=prediction_result.field_confidences,
            quality_score=prediction_result.quality_score,
            recommendations=prediction_result.recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting confidence: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict confidence")

@router.post("/analyze-pdf", response_model=TemplateGenerationResponse)
async def analyze_pdf_for_template(
    file: UploadFile = File(...),
    supplier_name: str = "",
    template_generator: TemplateGenerator = Depends(get_template_generator),
    pdf_extractor: PDFExtractor = Depends(get_pdf_extractor),
    template_manager: TemplateManager = Depends(get_template_manager),
    template_engine: TemplateEngine = Depends(get_template_engine)
):
    """Analyze a single PDF to suggest template patterns and extract data."""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Extract data from PDF
        extracted_data = pdf_extractor.extract(Path(tmp_file_path))
        
        # Auto-detect supplier name if not provided
        if not supplier_name:
            supplier_name = template_generator.extract_supplier_name(extracted_data.raw_text)
        
        # Try to find existing template for extraction
        template = template_manager.find_best_template(extracted_data.raw_text, supplier_name)
        field_mappings = {}
        
        if template:
            # Apply template to get extracted values
            try:
                processed_data = template_engine.apply_template(
                    template,
                    extracted_data.raw_text,
                    extracted_data.tables,
                    extracted_data.positioned_text
                )
                
                # Build field mappings with actual values
                field_mappings = {
                    "invoice_number": processed_data.invoice_number,
                    "invoice_date": _safe_date_isoformat(processed_data.invoice_date),
                    "supplier_name": processed_data.supplier_name,
                    "supplier_vat_number": processed_data.supplier_vat_number,
                    "customer_name": getattr(processed_data, 'customer_name', None),
                    "customer_vat_number": getattr(processed_data, 'customer_vat_number', None),
                    "total_amount": f"{processed_data.currency} {processed_data.total_amount:.2f}" if processed_data.total_amount else None,
                    "net_amount": f"{processed_data.currency} {processed_data.net_amount:.2f}" if processed_data.net_amount else None,
                    "vat_amount": f"{processed_data.currency} {processed_data.vat_amount:.2f}" if processed_data.vat_amount else None,
                    "payment_terms": getattr(processed_data, 'payment_terms', None),
                    "iban": getattr(processed_data, 'supplier_iban', None),
                    "line_items_count": len(processed_data.line_items)
                }
                
                # Remove None values
                field_mappings = {k: v for k, v in field_mappings.items() if v is not None}
                
            except Exception as e:
                logger.warning(f"Failed to extract values with template: {e}")
        
        # Generate template ID
        template_id = f"{supplier_name.lower().replace(' ', '_')}_analyzed"
        
        # Analyze PDF structure
        logger.info(f"Analyzing PDF {file.filename} for template generation")
        
        analysis_result = template_generator.analyze_single_pdf(
            pdf_path=Path(tmp_file_path),
            supplier_name=supplier_name,
            template_id=template_id
        )
        
        # Merge field mappings
        if field_mappings:
            analysis_result.field_mappings.update(field_mappings)
        
        return TemplateGenerationResponse(
            template_id=template_id,
            template_name=supplier_name,
            confidence_score=analysis_result.confidence_score,
            suggested_patterns=analysis_result.suggested_patterns,
            field_mappings=analysis_result.field_mappings,
            supplier_patterns=analysis_result.supplier_patterns,
            raw_text_preview=extracted_data.raw_text[:1000] + "..." if len(extracted_data.raw_text) > 1000 else extracted_data.raw_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze PDF")
    
    finally:
        # Clean up temporary file
        try:
            Path(tmp_file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file: {e}")

@router.post("/train-model", response_model=TrainingResponse)
async def train_model(request: TrainingRequest):
    """Train ML models with provided data."""
    
    try:
        # Sanitize and validate training data path to prevent path traversal
        training_path = Path(request.training_data_path).resolve()
        
        # Ensure the path is within allowed directories (security check)
        allowed_dirs = [Path("data").resolve(), Path("training").resolve(), Path("models").resolve()]
        if not any(str(training_path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
            raise HTTPException(status_code=403, detail="Training data path not allowed")
        
        if not training_path.exists():
            raise HTTPException(status_code=404, detail="Training data not found")
        
        # Generate training job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Start training based on model type
        if request.model_type == "template_generator":
            # Train template generator
            logger.info(f"Starting template generator training with job {job_id}")
            # TODO: Implement actual training
            return TrainingResponse(
                job_id=job_id,
                model_type=request.model_type,
                status="started",
                training_metrics=None
            )
        elif request.model_type == "pattern_analyzer":
            # Train pattern analyzer
            logger.info(f"Starting pattern analyzer training with job {job_id}")
            # TODO: Implement actual training
            return TrainingResponse(
                job_id=job_id,
                model_type=request.model_type,
                status="started",
                training_metrics=None
            )
        elif request.model_type == "confidence_predictor":
            # Train confidence predictor
            logger.info(f"Starting confidence predictor training with job {job_id}")
            # TODO: Implement actual training
            return TrainingResponse(
                job_id=job_id,
                model_type=request.model_type,
                status="started",
                training_metrics=None
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown model type: {request.model_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail="Failed to train model")

@router.get("/models")
async def list_models():
    """List available ML models and their status."""
    
    try:
        # TODO: Implement model listing
        return {
            "models": [
                {
                    "name": "template_generator",
                    "status": "available",
                    "version": "1.0.0",
                    "description": "Generates templates from sample PDFs"
                },
                {
                    "name": "pattern_analyzer", 
                    "status": "available",
                    "version": "1.0.0",
                    "description": "Analyzes text patterns for extraction rules"
                },
                {
                    "name": "confidence_predictor",
                    "status": "available", 
                    "version": "1.0.0",
                    "description": "Predicts extraction confidence scores"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models")

@router.get("/training-jobs/{job_id}")
async def get_training_job(job_id: str):
    """Get training job status."""
    
    # TODO: Implement training job tracking
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "metrics": {
            "accuracy": 0.95,
            "precision": 0.92,
            "recall": 0.88
        }
    }

@router.post("/test-template")
async def test_template_extraction(
    template_id: str = Form(...),
    file: UploadFile = File(...),
    template_manager: TemplateManager = Depends(get_template_manager),
    template_engine: TemplateEngine = Depends(get_template_engine),
    pdf_extractor: PDFExtractor = Depends(get_pdf_extractor)
):
    """Test template extraction with a PDF and show detailed results."""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Get template
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Extract data from PDF
        extracted_data = pdf_extractor.extract(Path(tmp_file_path))
        
        # Apply template
        processed_data = template_engine.apply_template(
            template,
            extracted_data.raw_text,
            extracted_data.tables,
            extracted_data.positioned_text
        )
        
        # Build detailed results
        field_extractions = {}
        extraction_details = {}
        
        for rule in template.extraction_rules:
            field_name = rule.field_name
            field_value = getattr(processed_data, field_name, None)
            confidence = processed_data.confidence_scores.get(field_name, 0.0)
            
            field_extractions[field_name] = field_value
            
            # Show which patterns matched
            matched_patterns = []
            for pattern in rule.patterns:
                matches = list(re.finditer(pattern.pattern, extracted_data.raw_text, re.IGNORECASE | re.MULTILINE))
                if matches:
                    matched_patterns.append({
                        "pattern": pattern.pattern,
                        "matches": [match.group() for match in matches[:3]],  # First 3 matches
                        "match_count": len(matches)
                    })
            
            extraction_details[field_name] = {
                "value": field_value,
                "confidence": confidence,
                "matched_patterns": matched_patterns,
                "found_by": "regex" if matched_patterns else "not_found"
            }
        
        return {
            "template_id": template_id,
            "template_name": template.name,
            "extracted_fields": field_extractions,
            "extraction_details": extraction_details,
            "confidence_scores": processed_data.confidence_scores,
            "line_items": processed_data.line_items,
            "raw_text_preview": extracted_data.raw_text[:1000] + "..." if len(extracted_data.raw_text) > 1000 else extracted_data.raw_text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing template: {e}")
        raise HTTPException(status_code=500, detail="Failed to test template")
    
    finally:
        # Clean up temporary file
        try:
            Path(tmp_file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file: {e}")

@router.post("/improve-template")
async def improve_template(
    template_id: str,
    sample_pdfs: List[str],
    template_generator: TemplateGenerator = Depends(get_template_generator),
    template_manager: TemplateManager = Depends(get_template_manager)
):
    """Improve existing template with additional sample PDFs."""
    
    try:
        # Get existing template
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Validate sample PDFs with path sanitization
        sample_paths = []
        for pdf_path in sample_pdfs:
            # Sanitize and validate file path to prevent path traversal
            path = Path(pdf_path).resolve()
            
            # Ensure the path is within allowed directories (security check)
            allowed_dirs = [Path("samples").resolve(), Path("tests").resolve(), Path("uploads").resolve()]
            if not any(str(path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
                raise HTTPException(status_code=403, detail=f"Sample PDF path not allowed: {pdf_path}")
            
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"Sample PDF not found: {pdf_path}")
            sample_paths.append(path)
        
        if not sample_paths:
            raise HTTPException(status_code=400, detail="At least one sample PDF is required")
        
        # Improve template
        logger.info(f"Improving template {template_id} with {len(sample_paths)} samples")
        
        improved_template = template_generator.improve_template(
            existing_template=template,
            additional_samples=sample_paths
        )
        
        # Save improved template
        template_manager.save_template(improved_template.template)
        
        return {
            "template_id": template_id,
            "improvements": improved_template.improvements,
            "confidence_score": improved_template.confidence_score,
            "message": "Template improved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error improving template: {e}")
        raise HTTPException(status_code=500, detail="Failed to improve template")