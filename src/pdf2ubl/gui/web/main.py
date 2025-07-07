"""FastAPI main application for PDF2UBL GUI."""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import logging
from typing import List, Optional

from ...api.templates import router as templates_router
from ...api.conversion import router as conversion_router
from ...api.ml import router as ml_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PDF2UBL GUI",
    description="Web interface for PDF2UBL - Convert PDF invoices to UBL XML",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(templates_router, prefix="/api/templates", tags=["templates"])
app.include_router(conversion_router, prefix="/api/conversion", tags=["conversion"])
app.include_router(ml_router, prefix="/api/ml", tags=["machine-learning"])

# Mount static files for frontend
static_path = Path(__file__).parent.parent / "frontend" / "build"
if static_path.exists():
    # Mount static files from the build directory
    app.mount("/static", StaticFiles(directory=str(static_path / "static")), name="static")
    # Also serve any other static assets from the build directory
    app.mount("/assets", StaticFiles(directory=str(static_path)), name="assets")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main web interface."""
    frontend_path = Path(__file__).parent.parent / "frontend" / "build" / "index.html"
    
    if frontend_path.exists():
        return HTMLResponse(content=frontend_path.read_text(), status_code=200)
    else:
        # Return a simple development page if frontend is not built
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PDF2UBL GUI</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { text-align: center; margin-bottom: 30px; }
                .card { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px; }
                .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }
                .btn:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>PDF2UBL GUI</h1>
                    <p>Web interface for PDF invoice to UBL XML conversion</p>
                </div>
                
                <div class="card">
                    <h3>🚀 Development Mode</h3>
                    <p>The React frontend is not built yet. You can still use the API:</p>
                    <ul>
                        <li><a href="/api/docs">API Documentation (Swagger)</a></li>
                        <li><a href="/api/redoc">API Documentation (ReDoc)</a></li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>📊 Quick Stats</h3>
                    <p>API endpoints available:</p>
                    <ul>
                        <li><strong>/api/templates</strong> - Template management</li>
                        <li><strong>/api/conversion</strong> - PDF to UBL conversion</li>
                        <li><strong>/api/ml</strong> - Machine learning features</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h3>🔧 Next Steps</h3>
                    <ol>
                        <li>Build the React frontend</li>
                        <li>Configure template management</li>
                        <li>Set up ML model training</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """, status_code=200)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "PDF2UBL GUI"}

@app.get("/api/info")
async def get_info():
    """Get application information."""
    return {
        "name": "PDF2UBL GUI",
        "version": "1.0.0",
        "description": "Web interface for PDF2UBL conversion",
        "endpoints": {
            "templates": "/api/templates",
            "conversion": "/api/conversion", 
            "ml": "/api/ml"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)