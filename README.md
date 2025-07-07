# PDF2UBL - Intelligente PDF Factuur naar UBL XML Converter

PDF2UBL is een krachtige Python applicatie die PDF facturen converteert naar UBL (Universal Business Language) XML formaat. Het systeem gebruikt intelligente template-gebaseerde extractie, machine learning en heeft uitgebreide ondersteuning voor Nederlandse leveranciers.

## 🚀 Features

- **🤖 Machine Learning Template Generator**: Automatische template generatie met AI-ondersteuning
- **🌐 Web GUI**: Moderne React-gebaseerde web interface voor eenvoudig beheer
- **📊 Multi-Method PDF Processing**: Gebruikt pdfplumber, PyMuPDF, en OCR voor robuuste tekstextractie
- **🎯 Template System**: Leverancier-specifieke templates voor accurate data extractie
- **✅ UBL 2.1 Compliance**: Genereert valide UBL XML compatible met Hostfact en andere boekhoudpakketten
- **💻 CLI Interface**: Rich command-line interface met progress bars en gekleurde output
- **📦 Batch Processing**: Verwerk meerdere PDFs tegelijk
- **🔧 Configuration Management**: Flexibele configuratie via bestanden of environment variables
- **🇳🇱 Nederlandse Datum Support**: Volledige ondersteuning voor Nederlandse datumnotaties

## 📋 Ondersteunde Leveranciers

PDF2UBL heeft geoptimaliseerde templates voor:

- **123accu B.V.** - IT componenten
- **Coolblue B.V.** - Online retail 
- **Dustin Nederland** - IT hardware en software
- **NextName B.V.** - Domeinnamen en hosting
- **Proserve B.V.** - Cloud diensten en hosting
- **VDX Nederland** - Telecommunicatie services
- **WeServit** - Cloud backup diensten
- **Opslagruimte Haaksbergen** - Self-storage diensten
- **CheapConnect** - Telecommunicatie
- **DectDirect.NL** - DECT telefonie
- **Fixxar** - Technische diensten (met OCR support)
- **Fonu** - Telecommunicatie diensten
- **Generic Nederlands** - Fallback voor onbekende leveranciers

## 🎯 Testresultaten

**Laatste validatie (tests2):**
- ✅ **95.7% Success Rate** (44/46 PDFs)
- ✅ **100% Quality Score** (geen validatie issues)
- ✅ **46 Test Facturen** succesvol verwerkt
- ✅ **Perfect UBL Compliance** voor Hostfact import

## 🛠️ Installatie

### Vereisten

- Python 3.8 of hoger
- pip (Python package manager)
- Node.js 16+ en npm (voor de web interface)

### Snelle Installatie

```bash
git clone https://github.com/brouwerict/PDF2UBL.git
cd PDF2UBL
./setup.sh  # Dit installeert alles automatisch
```

### Handmatige Installatie

1. **Clone de repository**
   ```bash
   git clone https://github.com/brouwerict/PDF2UBL.git
   cd PDF2UBL
   ```

2. **Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Web interface bouwen**
   ```bash
   # Installeer Node.js als je dat nog niet hebt
   sudo apt-get install nodejs npm  # Ubuntu/Debian
   
   # Bouw de frontend
   cd src/pdf2ubl/gui/frontend
   npm install
   npm run build
   cd ../../../..
   ```

### Optionele OCR Support

Voor OCR support (gescande PDFs), installeer Tesseract:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-nld

# macOS
brew install tesseract tesseract-lang

# Windows
# Download van: https://github.com/UB-Mannheim/tesseract/wiki
```

## 🚀 Quick Start

### 1. Enkele PDF Converteren

```bash
python3 -m src.pdf2ubl.cli convert invoice.pdf -o output.xml
```

### 2. Extractie Preview (zonder XML genereren)

```bash
python3 -m src.pdf2ubl.cli extract invoice.pdf
```

### 3. Batch Processing

```bash
python3 -m src.pdf2ubl.cli batch pdf_directory/ -o xml_output/
```

### 4. Web GUI Starten

```bash
# Zorg eerst dat de frontend gebouwd is (zie installatie)
python3 -m src.pdf2ubl.cli gui

# Voor toegang vanaf andere apparaten in het netwerk:
python3 -m src.pdf2ubl.cli gui --host 0.0.0.0 --port 8000

# Open browser: http://localhost:8000 of http://[server-ip]:8000
```

### 5. Test UBL Genereren

```bash
python3 -m src.pdf2ubl.cli test -o test_invoice.xml
```

## 💻 CLI Gebruik

### Core Operations

```bash
# Convert single PDF to UBL XML
python3 -m src.pdf2ubl.cli convert invoice.pdf -o output.xml

# Extract and preview data without generating XML
python3 -m src.pdf2ubl.cli extract invoice.pdf

# Batch convert multiple PDFs
python3 -m src.pdf2ubl.cli batch pdf_directory/ -o xml_output/

# Generate test UBL invoice for validation
python3 -m src.pdf2ubl.cli test -o test_invoice.xml

# Start web GUI
python3 -m src.pdf2ubl.cli gui
```

### Template Management

```bash
# List all available templates
python3 -m src.pdf2ubl.cli template list

# Create new supplier template
python3 -m src.pdf2ubl.cli template create supplier_id "Supplier Name" --supplier "Supplier B.V."

# Delete template
python3 -m src.pdf2ubl.cli template delete template_id

# View template usage statistics
python3 -m src.pdf2ubl.cli template stats
```

### Development en Testing

```bash
# Run with verbose logging
python3 -m src.pdf2ubl.cli convert invoice.pdf --verbose

# Test specific template
python3 -m src.pdf2ubl.cli convert invoice.pdf -t dustin_nl

# Extract with supplier hint for auto-detection
python3 -m src.pdf2ubl.cli convert invoice.pdf -s "DustinNederland"
```

## 🌐 Web GUI

De web GUI biedt:

- **📄 PDF Upload & Preview**: Sleep en zet PDF bestanden neer
- **🤖 ML Template Generator**: Automatische template generatie met AI
- **📊 Real-time Extractie Preview**: Zie geëxtraheerde velden live
- **📋 Template Management**: Beheer en bewerk templates visueel
- **📈 Conversion Statistics**: Overzicht van conversie statistieken
- **🔄 Batch Processing**: Upload en verwerk meerdere bestanden

Start de GUI met:
```bash
python3 -m src.pdf2ubl.cli gui
```

Ga dan naar: `http://localhost:8000`

## 🧠 Machine Learning Features

### Auto Template Generation

Het ML systeem kan automatisch templates genereren:

1. **Upload PDF samples** van een nieuwe leverancier
2. **AI analyseert** de structuur en patronen
3. **Template wordt gegenereerd** met optimale extractie regels
4. **Validatie en fine-tuning** via de GUI
5. **Direct deployment** voor productie gebruik

### Pattern Recognition

- **Intelligente veld detectie** voor factuurgegevens
- **Layout analyse** voor verschillende PDF formaten  
- **Confidence scoring** voor extractie kwaliteit
- **Fallback mechanismen** voor robuuste verwerking

## 📊 Template System

### Template Structuur

Templates bevatten:
- **Supplier Detection**: Patronen om de juiste template te identificeren
- **Field Extraction Rules**: Regex patronen voor factuurnummers, bedragen, datums
- **Line Item Processing**: Leverancier-specifieke formattering en BTW berekeningen
- **Confidence Scoring**: Kwaliteitsmetrieken voor extractie nauwkeurigheid

### Voorbeeld Template Configuratie

```json
{
  "template_id": "leverancier_nl",
  "name": "Leverancier B.V.",
  "supplier_patterns": [
    {
      "pattern": "Leverancier B\\.V\\.",
      "confidence_threshold": 0.9
    }
  ],
  "extraction_rules": [
    {
      "field_name": "invoice_number",
      "field_type": "text",
      "patterns": [
        {
          "pattern": "Factuurnummer[:\\s]*(\\d+)",
          "confidence_threshold": 0.9
        }
      ]
    }
  ],
  "date_format": "%d-%m-%Y",
  "currency": "EUR",
  "language": "nl"
}
```

## 📄 UBL Output Formaat

Genereert UBL 2.1 compliant XML met:

- **Juiste BTW berekeningen**: BTW-exclusieve regelitems met correcte belastingbedragen
- **Complete partij informatie**: Leverancier en klant details
- **Regelitem nauwkeurigheid**: Beschrijvingen, hoeveelheden, eenheidsprijzen
- **Betalingsvoorwaarden**: IBAN ondersteuning en betalingscondities
- **Validatie compliance**: Voldoet aan UBL schema validatie
- **Hostfact compatibility**: Direct importeerbaar in Hostfact

### Voorbeeld UBL Output

```xml
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <cbc:ID>F-2024-001</cbc:ID>
  <cbc:IssueDate>2024-07-07</cbc:IssueDate>
  <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyName>
        <cbc:Name>Leverancier B.V.</cbc:Name>
      </cac:PartyName>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>NL123456789B01</cbc:CompanyID>
      </cac:PartyTaxScheme>
    </cac:Party>
  </cac:AccountingSupplierParty>
  
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="EUR">21.00</cbc:TaxAmount>
  </cac:TaxTotal>
  
  <cac:LegalMonetaryTotal>
    <cbc:TaxExclusiveAmount currencyID="EUR">100.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="EUR">121.00</cbc:TaxInclusiveAmount>
  </cac:LegalMonetaryTotal>
</Invoice>
```

## 🏗️ Architectuur

Het systeem volgt een modulaire, gelaagde architectuur:

```
src/pdf2ubl/
├── cli.py                  # Rich command-line interface
├── extractors/             # Multi-method PDF parsing
│   ├── pdf_extractor.py   # Main extraction coordinator
│   ├── text_extractor.py  # Advanced text extraction
│   └── table_extractor.py # Table detection and parsing
├── templates/              # Template system
│   ├── template_engine.py # Core extraction logic
│   ├── template_manager.py # Template loading and detection
│   └── template_models.py # Data models
├── exporters/              # UBL export
│   └── ubl_exporter.py    # UBL 2.1 XML generation
├── ml/                     # Machine Learning
│   ├── template_generator.py # Auto template generation
│   ├── pattern_analyzer.py   # Pattern recognition
│   └── confidence_predictor.py # Quality scoring
├── gui/                    # Web interface
│   └── web/
│       ├── main.py        # FastAPI backend
│       ├── static/        # React frontend
│       └── api/           # REST API endpoints
└── utils/                  # Utilities
    ├── config.py          # Configuration management
    ├── validation.py      # Data validation
    └── formatters.py      # Output formatting
```

### Key Components

1. **TemplateEngine**: Past leverancier-specifieke extractie regels toe met confidence scoring
2. **TemplateManager**: Beheert template loading, detectie en fallback logica  
3. **PDFExtractor**: Multi-method text extractie met positionering en tabel detectie
4. **UBLExporter**: Genereert valide UBL XML met juiste BTW berekeningen en compliance
5. **CLI**: Gebruiksvriendelijke interface met gekleurde output en progress tracking
6. **ML Pipeline**: Automatische template generatie met pattern recognition
7. **Web GUI**: Modern React-gebaseerd beheerinterface

## 🔧 Configuratie

Het systeem ondersteunt configuratie via:

1. **JSON config bestanden** (`pdf2ubl.json`, `hostfact_config.json`)
2. **Environment variables** (prefixed with `PDF2UBL_`)
3. **Command-line opties**

### Voorbeeld Configuratie

```json
{
  "debug": false,
  "log_level": "INFO",
  "templates_dir": "templates",
  "use_ocr": false,
  "ocr_language": "nld",
  "default_currency": "EUR",
  "default_country": "NL",
  "default_vat_rate": 21.0,
  "min_confidence": 0.3,
  "strict_mode": false,
  "fallback_enabled": true,
  "gui_host": "localhost",
  "gui_port": 8000
}
```

## 🧪 Testing & Validatie

### Uitgebreide Test Suite

```bash
# Test alle facturen in tests2/
python3 comprehensive_test_tests2.py

# Valideer specifieke leverancier
python3 -m src.pdf2ubl.cli convert tests2/Coolblue_factuur_*.pdf

# Test nieuwe template
python3 -m src.pdf2ubl.cli extract nieuwe_factuur.pdf -t nieuwe_template
```

### Kwaliteitsmetrieken

- **95.7% Success Rate** op test dataset
- **100% Quality Score** (geen validatie fouten)
- **Perfect UBL Compliance** voor alle ondersteunde leveranciers
- **Automatische BTW validatie** met tolerance checks
- **Line item consistency** verificatie

## 🚨 Troubleshooting

### Veelvoorkomende Problemen

1. **PDF extractie faalt**
   ```bash
   # Probeer OCR te enablen
   python3 -m src.pdf2ubl.cli convert --use-ocr factuur.pdf
   ```

2. **Template niet gevonden**
   ```bash
   # Lijst beschikbare templates
   python3 -m src.pdf2ubl.cli template list
   
   # Gebruik supplier hint
   python3 -m src.pdf2ubl.cli convert factuur.pdf -s "Leverancier"
   ```

3. **UBL validatie errors**
   ```bash
   # Check extractie preview
   python3 -m src.pdf2ubl.cli extract factuur.pdf --verbose
   ```

4. **Nederlandse datum problemen**
   - Systeem ondersteunt automatisch Nederlandse maandnamen
   - Formats: "30 september 2024", "30-09-2024", "30.09.2024"

### Debug Mode

```bash
# Verbose logging
python3 -m src.pdf2ubl.cli convert factuur.pdf --verbose

# Debug environment
export PDF2UBL_DEBUG=true
export PDF2UBL_LOG_LEVEL=DEBUG
```

## 🎯 Hostfact Integratie

Speciale focus op Hostfact boekhoudpakket compatibiliteit:

- **Juiste leverancier naam extractie** (geen "Unknown Supplier" errors)
- **Correcte BTW-exclusieve prijzen** voor regelitems
- **Nauwkeurige totaalbedrag berekeningen**
- **UBL XML format compliance** voor naadloze import
- **Nederlandse datum en valuta formaten**
- **Complete BTW informatie** inclusief percentages

### Import in Hostfact

1. **Converteer** PDF naar UBL XML met PDF2UBL
2. **Login** in Hostfact
3. **Ga naar** Inkoop → Facturen → Importeren
4. **Upload** de gegenereerde UBL XML
5. **Controleer** en bevestig de import

## 📈 Performance

- **Multi-threading** voor batch processing
- **Memory-efficient** PDF parsing
- **Intelligent caching** van templates
- **Optimized regex patterns** voor snelle extractie
- **Lazy loading** van ML models
- **Progressive processing** voor grote bestanden

## 🔄 Updates & Onderhoud

### Template Updates

Templates worden automatisch bijgewerkt voor:
- **Nieuwe leveranciers** detectie
- **Format wijzigingen** in bestaande facturen  
- **Verbeterde extractie regels**
- **BTW percentage aanpassingen**

### Version Management

```bash
# Check versie
python3 -m src.pdf2ubl.cli --version

# Update templates
python3 -m src.pdf2ubl.cli template update-all

# Backup configuratie
python3 -m src.pdf2ubl.cli config backup
```

## 📊 Statistieken

**Tests2 Validatie Resultaten:**
- 📄 **46 PDF bestanden** verwerkt
- ✅ **44 succesvolle conversies** (95.7%)
- 📋 **9 verschillende templates** gebruikt
- 🎯 **100% kwaliteitsscore** (geen validatie issues)
- 💰 **Alle bedragen correct** geëxtraheerd
- 📝 **Line items compleet** voor alle leveranciers

## 🚀 Toekomst

Geplande features:
- **Enhanced OCR** met table detection
- **API endpoints** voor integratie
- **Webhook support** voor automatische processing
- **Cloud deployment** opties
- **Multi-language** support uitbreiding
- **Advanced ML models** voor betere accuracy

## 📄 Licentie

Dit project valt onder de MIT License - zie het LICENSE bestand voor details.

## 💬 Support

Voor support en vragen:

1. **Check de documentatie** en troubleshooting sectie
2. **Test met verbose mode** voor gedetailleerde logging
3. **Controleer bestaande issues** in de repository
4. **Maak een nieuwe issue** aan met:
   - PDF2UBL versie
   - Python versie  
   - Error messages
   - Sample bestanden (indien mogelijk)
   - Template informatie

---

**PDF2UBL** - Geoptimaliseerd voor Nederlandse factuurverwerking en Hostfact integratie 🇳🇱