"""Conversion API router for PDF2UBL GUI."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import tempfile
import logging
import uuid
import json
import zipfile
import io
from datetime import datetime

from ..extractors.pdf_extractor import PDFExtractor
from ..exporters.ubl_exporter import UBLExporter
from ..templates.template_manager import TemplateManager
from ..templates.template_engine import TemplateEngine

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for API
class ConversionRequest(BaseModel):
    """Request model for PDF conversion."""
    template_id: Optional[str] = None
    supplier_hint: Optional[str] = None
    preview_only: bool = False

class ConversionResponse(BaseModel):
    """Response model for PDF conversion."""
    job_id: str
    status: str
    message: str
    pdf_filename: str
    template_used: Optional[str] = None
    extraction_data: Optional[Dict[str, Any]] = None
    ubl_xml: Optional[str] = None
    confidence_scores: Optional[Dict[str, float]] = None
    created_at: str

class ExtractionPreview(BaseModel):
    """Preview model for extraction data."""
    template_used: str
    confidence_scores: Dict[str, float]
    extracted_fields: Dict[str, Any]
    line_items: List[Dict[str, Any]]
    raw_text_preview: str

class ConversionJob(BaseModel):
    """Model for conversion job tracking."""
    job_id: str
    status: str  # pending, processing, completed, failed
    pdf_filename: str
    template_id: Optional[str] = None
    supplier_hint: Optional[str] = None
    preview_only: bool = False
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# In-memory job storage (in production, use Redis or database)
conversion_jobs: Dict[str, ConversionJob] = {}

# Dependency to get components
def get_pdf_extractor():
    """Get PDF extractor instance."""
    return PDFExtractor()

def get_template_manager():
    """Get template manager instance."""
    return TemplateManager()

def get_template_engine():
    """Get template engine instance."""
    return TemplateEngine()

def get_ubl_exporter():
    """Get UBL exporter instance."""
    return UBLExporter()

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

@router.post("/upload", response_model=ConversionResponse)
async def upload_and_convert(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    template_id: Optional[str] = None,
    supplier_hint: Optional[str] = None,
    preview_only: bool = False
):
    """Upload PDF and convert to UBL XML."""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Create conversion job
        job = ConversionJob(
            job_id=job_id,
            status="pending",
            pdf_filename=file.filename,
            template_id=template_id,
            supplier_hint=supplier_hint,
            preview_only=preview_only,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        conversion_jobs[job_id] = job
        
        # Start background conversion
        background_tasks.add_task(
            process_conversion,
            job_id,
            tmp_file_path,
            template_id,
            supplier_hint,
            preview_only
        )
        
        return ConversionResponse(
            job_id=job_id,
            status="pending",
            message="PDF upload successful, conversion started",
            pdf_filename=file.filename,
            created_at=job.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

async def process_conversion(
    job_id: str,
    pdf_path: str,
    template_id: Optional[str] = None,
    supplier_hint: Optional[str] = None,
    preview_only: bool = False
):
    """Process PDF conversion in background."""
    
    job = conversion_jobs.get(job_id)
    if not job:
        return
    
    try:
        # Update job status
        job.status = "processing"
        job.updated_at = datetime.now()
        
        # Initialize components
        pdf_extractor = PDFExtractor()
        template_manager = TemplateManager()
        template_engine = TemplateEngine()
        ubl_exporter = UBLExporter()
        
        # Extract data from PDF
        logger.info(f"Extracting data from PDF: {pdf_path}")
        extracted_data = pdf_extractor.extract(Path(pdf_path))
        
        # Find or use template
        selected_template = None
        if template_id:
            selected_template = template_manager.get_template(template_id)
            if not selected_template:
                raise ValueError(f"Template not found: {template_id}")
        else:
            # Auto-detect template
            selected_template = template_manager.find_best_template(
                extracted_data.raw_text, supplier_hint
            )
            if not selected_template:
                selected_template = template_manager.get_default_template()
        
        if not selected_template:
            raise ValueError("No template available for processing")
        
        # Apply template to extract structured data
        logger.info(f"Applying template: {selected_template.name}")
        processed_data = template_engine.apply_template(
            selected_template,
            extracted_data.raw_text,
            extracted_data.tables,
            extracted_data.positioned_text
        )
        
        # Prepare result
        result = {
            "template_used": selected_template.template_id,
            "template_name": selected_template.name,
            "confidence_scores": processed_data.confidence_scores,
            "extracted_fields": {
                "invoice_number": processed_data.invoice_number,
                "invoice_date": _safe_date_isoformat(processed_data.invoice_date),
                "supplier_name": processed_data.supplier_name,
                "supplier_vat_number": processed_data.supplier_vat_number,
                "total_amount": processed_data.total_amount,
                "net_amount": processed_data.net_amount,
                "vat_amount": processed_data.vat_amount,
                "currency": processed_data.currency,
            },
            "line_items": processed_data.line_items,
            "raw_text_preview": extracted_data.raw_text[:500] + "..." if len(extracted_data.raw_text) > 500 else extracted_data.raw_text
        }
        
        # Generate UBL XML if not preview only
        if not preview_only:
            logger.info("Generating UBL XML")
            ubl_xml = ubl_exporter.export_to_ubl(processed_data)
            result["ubl_xml"] = ubl_xml
        
        # Update job with success
        job.status = "completed"
        job.result = result
        job.updated_at = datetime.now()
        
        logger.info(f"Conversion completed successfully for job {job_id}")
        
    except Exception as e:
        logger.error(f"Conversion failed for job {job_id}: {e}")
        job.status = "failed"
        job.error = str(e)
        job.updated_at = datetime.now()
    
    finally:
        # Clean up temporary file
        try:
            Path(pdf_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {pdf_path}: {e}")

@router.get("/jobs/{job_id}", response_model=ConversionResponse)
async def get_conversion_job(job_id: str):
    """Get conversion job status and results."""
    
    job = conversion_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = ConversionResponse(
        job_id=job.job_id,
        status=job.status,
        message=_get_status_message(job.status, job.error),
        pdf_filename=job.pdf_filename,
        created_at=job.created_at.isoformat()
    )
    
    # Add result data if available
    if job.result:
        response.template_used = job.result.get("template_used")
        response.confidence_scores = job.result.get("confidence_scores")
        response.extraction_data = job.result.get("extracted_fields")
        response.ubl_xml = job.result.get("ubl_xml")
    
    return response

@router.get("/jobs", response_model=List[ConversionResponse])
async def list_conversion_jobs(limit: int = 50, offset: int = 0):
    """List recent conversion jobs."""
    
    # Sort jobs by creation date (newest first)
    sorted_jobs = sorted(conversion_jobs.values(), key=lambda x: x.created_at, reverse=True)
    
    # Apply pagination
    paginated_jobs = sorted_jobs[offset:offset + limit]
    
    return [
        ConversionResponse(
            job_id=job.job_id,
            status=job.status,
            message=_get_status_message(job.status, job.error),
            pdf_filename=job.pdf_filename,
            template_used=job.result.get("template_used") if job.result else None,
            created_at=job.created_at.isoformat()
        )
        for job in paginated_jobs
    ]

@router.delete("/jobs/{job_id}")
async def delete_conversion_job(job_id: str):
    """Delete a conversion job."""
    
    if job_id not in conversion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del conversion_jobs[job_id]
    return {"message": "Job deleted successfully"}

@router.post("/preview", response_model=ExtractionPreview)
async def preview_extraction(
    file: UploadFile = File(...),
    template_id: Optional[str] = None,
    supplier_hint: Optional[str] = None,
    pdf_extractor: PDFExtractor = Depends(get_pdf_extractor),
    template_manager: TemplateManager = Depends(get_template_manager),
    template_engine: TemplateEngine = Depends(get_template_engine)
):
    """Preview extraction without generating UBL XML."""
    
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
        
        # Find or use template
        selected_template = None
        if template_id:
            selected_template = template_manager.get_template(template_id)
            if not selected_template:
                raise HTTPException(status_code=404, detail="Template not found")
        else:
            # Auto-detect template
            selected_template = template_manager.find_best_template(
                extracted_data.raw_text, supplier_hint
            )
            if not selected_template:
                selected_template = template_manager.get_default_template()
        
        if not selected_template:
            raise HTTPException(status_code=500, detail="No template available for processing")
        
        # Apply template to extract structured data
        processed_data = template_engine.apply_template(
            selected_template,
            extracted_data.raw_text,
            extracted_data.tables,
            extracted_data.positioned_text
        )
        
        return ExtractionPreview(
            template_used=selected_template.template_id,
            confidence_scores=processed_data.confidence_scores,
            extracted_fields={
                "invoice_number": processed_data.invoice_number,
                "invoice_date": _safe_date_isoformat(processed_data.invoice_date),
                "supplier_name": processed_data.supplier_name,
                "supplier_vat_number": processed_data.supplier_vat_number,
                "total_amount": processed_data.total_amount,
                "net_amount": processed_data.net_amount,
                "vat_amount": processed_data.vat_amount,
                "currency": processed_data.currency,
            },
            line_items=processed_data.line_items,
            raw_text_preview=extracted_data.raw_text[:500] + "..." if len(extracted_data.raw_text) > 500 else extracted_data.raw_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing extraction: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview extraction")
    
    finally:
        # Clean up temporary file
        try:
            Path(tmp_file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file: {e}")

@router.post("/batch")
async def batch_convert(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    template_id: Optional[str] = None,
    supplier_hint: Optional[str] = None
):
    """Upload multiple PDFs for batch conversion."""
    
    if len(files) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
    
    batch_id = str(uuid.uuid4())
    job_ids = []
    
    try:
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                logger.warning(f"Skipping non-PDF file: {file.filename}")
                continue
            
            # Generate job ID
            job_id = str(uuid.uuid4())
            job_ids.append(job_id)
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            # Create conversion job
            job = ConversionJob(
                job_id=job_id,
                status="pending",
                pdf_filename=file.filename,
                template_id=template_id,
                supplier_hint=supplier_hint,
                preview_only=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            conversion_jobs[job_id] = job
            
            # Start background conversion
            background_tasks.add_task(
                process_conversion,
                job_id,
                tmp_file_path,
                template_id,
                supplier_hint,
                False
            )
        
        return {
            "batch_id": batch_id,
            "job_ids": job_ids,
            "message": f"Batch conversion started with {len(job_ids)} files"
        }
        
    except Exception as e:
        logger.error(f"Error in batch conversion: {e}")
        raise HTTPException(status_code=500, detail="Failed to process batch conversion")

@router.get("/jobs/{job_id}/download")
async def download_ubl_xml(job_id: str):
    """Download UBL XML file for a completed conversion job."""
    
    job = conversion_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Conversion not completed yet")
    
    if not job.result or not job.result.get("ubl_xml"):
        raise HTTPException(status_code=404, detail="UBL XML not available")
    
    ubl_xml = job.result["ubl_xml"]
    filename = f"{job.pdf_filename.replace('.pdf', '')}.xml"
    
    return Response(
        content=ubl_xml,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/batch/{batch_id}/download")
async def download_batch_zip(batch_id: str, job_ids: str = Query(..., description="Comma-separated list of job IDs")):
    """Download ZIP file containing all UBL XML files for a batch of jobs."""
    
    # Parse job IDs from comma-separated string
    if not job_ids:
        raise HTTPException(status_code=400, detail="No job IDs provided")
    
    job_id_list = [job_id.strip() for job_id in job_ids.split(',') if job_id.strip()]
    
    if not job_id_list:
        raise HTTPException(status_code=400, detail="No valid job IDs provided")
    
    # Check if all jobs exist and are completed
    xml_files = []
    for job_id in job_id_list:
        job = conversion_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        if job.status != "completed":
            raise HTTPException(status_code=400, detail=f"Job {job_id} not completed yet")
        
        if not job.result or not job.result.get("ubl_xml"):
            logger.warning(f"No UBL XML available for job {job_id}")
            continue
        
        xml_files.append({
            'filename': f"{job.pdf_filename.replace('.pdf', '')}.xml",
            'content': job.result["ubl_xml"]
        })
    
    if not xml_files:
        raise HTTPException(status_code=404, detail="No UBL XML files available for download")
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for xml_file in xml_files:
            zip_file.writestr(xml_file['filename'], xml_file['content'])
    
    zip_buffer.seek(0)
    
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}.zip"}
    )

def _get_status_message(status: str, error: Optional[str] = None) -> str:
    """Get human-readable status message."""
    if status == "pending":
        return "Conversion job is queued"
    elif status == "processing":
        return "Converting PDF to UBL XML"
    elif status == "completed":
        return "Conversion completed successfully"
    elif status == "failed":
        return f"Conversion failed: {error}" if error else "Conversion failed"
    else:
        return f"Unknown status: {status}"