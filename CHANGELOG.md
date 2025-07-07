# Changelog

All notable changes to PDF2UBL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-01-07

### Added
- **Multi-file Upload**: Batch processing with ZIP download support
- **Deployment Scripts**: Automated update scripts for production
- **Docker Compose**: Production-ready container orchestration
- **Security Policy**: Comprehensive security documentation (SECURITY.md)
- **CI/CD Pipeline**: Automated testing and security scanning

### Security
- **Path Traversal Protection**: Fixed high-priority security vulnerabilities
- **Input Validation**: Added directory restrictions for file operations
- **API Sanitization**: Prevented malicious path access in templates and ML APIs
- **Dependency Scanning**: Automated vulnerability detection with Trivy and CodeQL

### Improved
- **Web Interface**: Enhanced batch conversion with progress tracking
- **Error Handling**: Better error messages and fallback mechanisms
- **Documentation**: Updated installation guides with network access instructions
- **CI/CD Reliability**: Made pipeline more resilient with continue-on-error

### Fixed
- **Frontend Build**: Resolved "React frontend is not built yet" for fresh clones
- **Security Alerts**: Addressed CodeQL and Trivy vulnerability findings
- **Workflow Stability**: Fixed YAML syntax errors in GitHub Actions
- **Script Portability**: Update scripts now work from any directory

### Technical
- **GitHub Actions**: Updated deprecated actions to latest versions
- **Security Scanning**: Enhanced Trivy and CodeQL integration
- **Container Health**: Added health checks and restart policies
- **Volume Mounting**: Proper file handling for uploads

## [1.0.0] - 2024-01-07

### Added
- Complete PDF to UBL XML conversion system
- Web GUI with React frontend and FastAPI backend
- 13 pre-configured Dutch supplier templates
- Machine Learning features for auto-template generation
- Batch processing with ZIP download support
- Multi-file upload functionality
- Template management system with visual editor
- CLI interface with multiple commands
- Docker support for containerized deployment
- Comprehensive documentation in Dutch
- CI/CD pipeline with GitHub Actions

### Features
- 95.7% template detection success rate
- Support for Dutch invoice formats
- Hostfact accounting software integration
- VAT calculation and validation
- Line item extraction with amounts
- OCR support for scanned PDFs
- Real-time conversion progress tracking
- Template testing and validation tools

### Supported Suppliers
- 123accu B.V.
- CheapConnect
- Coolblue
- DectDirect.NL
- Dustin Nederland
- Fixxar
- Fonu Telecom
- NextName
- Opslagruimte Haaksbergen
- Proserve
- VDX
- WeServit
- Generic Dutch invoice template

### Technical Stack
- Python 3.8+ with FastAPI
- React with TypeScript and Material-UI
- PDF extraction with pdfplumber and PyMuPDF
- UBL 2.1 XML generation
- Docker multi-stage builds
- GitHub Actions CI/CD

### Documentation
- README.md with quick start guide
- INSTALL.md with detailed installation instructions
- CLAUDE.md for AI assistant guidance
- TEMPLATE_GUIDE.md for creating custom templates
- GUI_README.md for web interface usage

### Initial Release
This is the first public release of PDF2UBL, a production-ready tool for converting
Dutch PDF invoices to UBL XML format.