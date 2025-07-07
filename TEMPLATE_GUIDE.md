# 📋 Template Gids - PDF2UBL

## 🎯 Wat zijn Templates?

Templates zijn configuratiebestanden die het systeem vertellen hoe specifieke factuurformaten moeten worden gelezen. Elke leverancier heeft vaak een uniek factuurformat, dus met templates kun je de extractie optimaliseren voor specifieke bedrijven.

## 🚀 Basis Commando's

### Template Beheer
```bash
# Bekijk alle templates
python3 -m src.pdf2ubl.cli template list

# Maak nieuwe template
python3 -m src.pdf2ubl.cli template create [ID] [NAME] --supplier [LEVERANCIER]

# Verwijder template
python3 -m src.pdf2ubl.cli template delete [ID]

# Template statistieken
python3 -m src.pdf2ubl.cli template stats
```

### Template Gebruiken
```bash
# Gebruik specifieke template
python3 -m src.pdf2ubl.cli convert factuur.pdf -t mediamarkt_nl

# Automatische detectie met hint
python3 -m src.pdf2ubl.cli convert factuur.pdf -s "MediaMarkt"

# Preview met template
python3 -m src.pdf2ubl.cli extract factuur.pdf -t ah_nl
```

## 🛠️ Template Maken - Stap voor Stap

### Stap 1: Basis Template Aanmaken
```bash
python3 -m src.pdf2ubl.cli template create mijn_leverancier_nl "Mijn Leverancier" --supplier "Mijn Leverancier B.V." --description "Custom template"
```

### Stap 2: JSON Bestand Aanpassen
Het template wordt opgeslagen in `templates/mijn_leverancier_nl.json`. Je kunt deze bewerken om specifieke patronen toe te voegen.

### Stap 3: Patronen Definiëren

#### Invoice Number Patronen
```json
{
  "field_name": "invoice_number",
  "patterns": [
    {
      "pattern": "Factuurnummer[:\\s]+([A-Za-z0-9\\-/]+)",
      "method": "regex",
      "confidence_threshold": 0.9,
      "priority": 15,
      "name": "Mijn factuur nummer patroon"
    }
  ]
}
```

#### Bedrag Patronen
```json
{
  "field_name": "total_amount", 
  "patterns": [
    {
      "pattern": "Totaal[:\\s]*€\\s*(\\d+[.,]\\d{2})",
      "method": "regex",
      "confidence_threshold": 0.9,
      "priority": 12,
      "name": "Mijn totaal bedrag patroon"
    }
  ]
}
```

## 🎨 Template Voorbeelden

### 1. MediaMarkt Template
- **Invoice numbers**: `MM-123456` format
- **Specifieke velden**: "Totaalbedrag" ipv "Totaal"
- **BTW format**: "BTW 21%"

### 2. Albert Heijn Template  
- **Invoice numbers**: "Bonnummer" met 10+ cijfers
- **Retail format**: Andere terminologie
- **Producten**: Line items als boodschappen

### 3. Coolblue Template
- **Webshop format**: Online bestelnummer
- **Tracking info**: Verzendgegevens
- **Product codes**: SKU nummers

## ⚡ Geavanceerde Features

### 1. Automatische Leverancier Detectie
Templates kunnen automatisch worden geselecteerd op basis van tekst in de factuur:

```json
{
  "supplier_patterns": [
    {
      "pattern": "MediaMarkt",
      "method": "regex", 
      "confidence_threshold": 0.9
    }
  ]
}
```

### 2. Prioriteit Systeem
Hogere priority nummers worden eerst geprobeerd:

```json
{
  "priority": 15,  // Hoge prioriteit - wordt eerst geprobeerd
  "priority": 5    // Lage prioriteit - fallback
}
```

### 3. Validation Patterns
Controleer of geëxtraheerde waarden geldig zijn:

```json
{
  "pattern": "([A-Z]{2}\\d{9}B\\d{2})",
  "validation_pattern": "^[A-Z]{2}\\d{9}B\\d{2}$",
  "name": "BTW nummer validatie"
}
```

### 4. Multi-line Patronen
Voor complexe facturen die meerdere regels beslaan:

```json
{
  "pattern": "Klantnummer\\s+Factuurnummer[\\s\\S]*?\\n[\\s]*\\d+\\s+([A-Za-z0-9\\-/]+)",
  "multiline": true,
  "confidence_threshold": 0.9
}
```

## 🎯 Use Cases

### Voor Freelancers/ZZP
- **Template per klant**: Elke klant heeft eigen factuurformat
- **Automatische verwerking**: Batch alle facturen van 1 leverancier
- **Boekhoudintegratie**: Direct naar Hostfact/andere systemen

### Voor Bedrijven  
- **Leverancier templates**: Per leverancier geoptimaliseerd
- **Departement-specifiek**: Verschillende afdelingen, verschillende formats
- **Compliance**: Ensure alle verplichte velden worden geëxtraheerd

### Voor Accountants
- **Klant-specifieke templates**: Per klant aangepaste extractie
- **Bulk processing**: Batch verwerking van alle klanten
- **Quality control**: Template success rates monitoren

## 📊 Template Prestaties Monitoren

```bash
# Bekijk template statistieken
python3 -m src.pdf2ubl.cli template stats

# Test template tegen factuur
python3 -m src.pdf2ubl.cli extract factuur.pdf -t mijn_template

# Batch test alle facturen
python3 test_all_invoices.py
```

## 🔧 Troubleshooting

### Template wordt niet gebruikt
1. Check template ID spelling
2. Verificeer supplier patterns
3. Test met `-v` verbose flag

### Lage extraction quality
1. Verhoog pattern priorities  
2. Voeg meer specifieke patronen toe
3. Test regex patterns apart

### Template conflicts
1. Check pattern priorities
2. Gebruik specifiekere patronen
3. Test met verschillende facturen

## 💡 Best Practices

1. **Start met generic_nl** - Kopieer en pas aan
2. **Test incrementeel** - Voeg 1 patroon per keer toe  
3. **Gebruik descriptive names** - Voor debugging
4. **Documenteer patronen** - Voeg beschrijvingen toe
5. **Monitor success rates** - Bekijk template stats regelmatig

## 🚀 Volgende Stappen

1. **Maak je eerste template** voor een veelgebruikte leverancier
2. **Test met echte facturen** uit je administratie  
3. **Optimaliseer patronen** op basis van resultaten
4. **Automatiseer** met batch processing
5. **Monitor** en verbeter success rates

---

*📞 Hulp nodig? Check de CLI help: `python3 -m src.pdf2ubl.cli --help`*