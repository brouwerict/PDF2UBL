# PDF2UBL GUI

A modern web interface for PDF2UBL that makes it easy to convert PDF invoices to UBL XML format, manage templates, and leverage ML-powered features.

## Features

### 🚀 Core Features
- **PDF to UBL Conversion**: Drag & drop PDF files for instant conversion
- **Template Management**: Create, edit, and manage supplier-specific templates
- **Real-time Progress**: Track conversion jobs with live updates
- **Batch Processing**: Convert multiple PDFs simultaneously
- **Preview Mode**: Extract and preview data without generating XML

### 🤖 ML-Powered Features
- **Auto-Template Generation**: Create templates from sample PDFs using ML
- **Pattern Analysis**: Intelligent pattern suggestions for field extraction
- **Confidence Prediction**: Get quality scores for extractions
- **Template Improvement**: Enhance existing templates with additional samples

### 📊 Dashboard & Analytics
- **Conversion Statistics**: Success rates, usage metrics, and trends
- **Template Performance**: Track which templates work best
- **Recent Activity**: Monitor latest conversions and their status
- **Visual Charts**: Bar charts and pie charts for data insights

## Quick Start

### 1. Start the Backend
```bash
# From the project root
python start_gui.py
```

The backend will start at `http://localhost:8000` with a development interface.

### 2. Build the Frontend (Optional)
For the full React interface:

```bash
# Navigate to frontend directory
cd src/pdf2ubl/gui/frontend

# Install dependencies
npm install

# Build for production
npm run build

# Or run in development mode
npm start
```

### 3. Access the Interface
- **Main Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Alternative API Docs**: http://localhost:8000/api/redoc

## Architecture

### Backend (FastAPI)
```
src/pdf2ubl/
├── gui/
│   └── web/
│       └── main.py          # FastAPI application
├── api/
│   ├── templates.py         # Template management API
│   ├── conversion.py        # PDF conversion API
│   └── ml.py               # ML features API
└── ml/
    ├── template_generator.py # Auto-template generation
    ├── pattern_analyzer.py   # Pattern analysis
    └── confidence_predictor.py # Quality prediction
```

### Frontend (React + TypeScript)
```
src/pdf2ubl/gui/frontend/
├── src/
│   ├── components/         # Reusable UI components
│   ├── pages/             # Main application pages
│   ├── services/          # API service layer
│   └── utils/             # Utility functions
├── public/                # Static assets
└── package.json           # Dependencies
```

## API Endpoints

### Templates
- `GET /api/templates/` - List all templates
- `POST /api/templates/` - Create new template
- `GET /api/templates/{id}` - Get template details
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

### Conversion
- `POST /api/conversion/upload` - Upload and convert PDF
- `POST /api/conversion/preview` - Preview extraction
- `GET /api/conversion/jobs/{id}` - Get conversion status
- `POST /api/conversion/batch` - Batch convert PDFs

### ML Features
- `POST /api/ml/generate-template` - Generate template from samples
- `POST /api/ml/analyze-patterns` - Analyze text patterns
- `POST /api/ml/predict-confidence` - Predict extraction quality
- `POST /api/ml/analyze-pdf` - Analyze single PDF

## Usage Examples

### 1. Convert a PDF
1. Go to the **Convert** page
2. Select a template (optional) or use auto-detection
3. Drag & drop your PDF file
4. Download the generated UBL XML

### 2. Create a Template
1. Go to **Templates** → **New Template**
2. Upload sample PDFs from a supplier
3. Let ML analyze and suggest patterns
4. Review and adjust the generated template
5. Save for future conversions

### 3. Batch Processing
1. Go to the **Convert** page
2. Select multiple PDF files
3. Choose a template or supplier hint
4. Monitor progress on the dashboard

### 4. ML Analysis
1. Go to **ML Features**
2. Upload a PDF for analysis
3. Get suggested patterns and confidence scores
4. Use insights to improve templates

## Configuration

### Environment Variables
```bash
PDF2UBL_TEMPLATES_DIR=./templates    # Template storage directory
PDF2UBL_LOG_LEVEL=INFO              # Logging level
PDF2UBL_MAX_FILE_SIZE=50MB          # Maximum upload size
```

### Template Configuration
Templates are stored as JSON files in the `templates/` directory and can be managed through the web interface.

## Development

### Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
python start_gui.py
```

### Frontend Development
```bash
cd src/pdf2ubl/gui/frontend

# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Adding New Features
1. **Backend**: Add new endpoints in `src/pdf2ubl/api/`
2. **Frontend**: Create components in `src/pdf2ubl/gui/frontend/src/`
3. **ML**: Add ML components in `src/pdf2ubl/ml/`

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation and settings
- **scikit-learn**: Machine learning
- **transformers**: NLP capabilities

### Frontend
- **React**: UI library
- **TypeScript**: Type safety
- **Material-UI**: Component library
- **React Query**: Data fetching
- **Recharts**: Data visualization

## Troubleshooting

### Common Issues

1. **Frontend not loading**: Build the React app with `npm run build`
2. **PDF upload fails**: Check file size limits and format
3. **Template not found**: Ensure templates are in the correct directory
4. **ML features not working**: Verify scikit-learn installation

### Debug Mode
Run with verbose logging:
```bash
python start_gui.py --verbose
```

### Health Check
Visit `http://localhost:8000/health` to verify the backend is running.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project follows the same license as the main PDF2UBL application.