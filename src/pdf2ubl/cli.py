#!/usr/bin/env python3
"""Command-line interface for PDF2UBL."""

import click
import sys
from pathlib import Path
import logging

from . import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version=__version__, prog_name="PDF2UBL")
def cli():
    """PDF2UBL - Convert PDF invoices to UBL XML format."""
    pass

@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
def gui(host, port, reload):
    """Start the web GUI interface."""
    try:
        import uvicorn
    except ImportError:
        click.echo("Error: uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)
    
    click.echo(f"Starting PDF2UBL Web GUI v{__version__}...")
    
    # Import the FastAPI app
    from .gui.web.main import app
    
    # Run the server
    uvicorn.run(
        "src.pdf2ubl.gui.web.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True))
@click.option('-o', '--output', help='Output XML file path')
@click.option('-t', '--template', help='Template ID to use')
@click.option('-s', '--supplier', help='Supplier hint for auto-detection')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def convert(pdf_file, output, template, supplier, verbose):
    """Convert a PDF invoice to UBL XML."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    from .extractors.pdf_extractor import PDFExtractor
    from .templates.template_manager import TemplateManager
    from .templates.template_engine import TemplateEngine
    from .exporters.ubl_exporter import UBLExporter
    
    try:
        # Extract data from PDF
        click.echo(f"Extracting data from {pdf_file}...")
        extractor = PDFExtractor()
        extracted_data = extractor.extract(Path(pdf_file))
        
        # Find template
        manager = TemplateManager()
        if template:
            tmpl = manager.get_template(template)
            if not tmpl:
                click.echo(f"Error: Template '{template}' not found", err=True)
                sys.exit(1)
        else:
            tmpl = manager.find_best_template(extracted_data.raw_text, supplier)
            if not tmpl:
                tmpl = manager.get_default_template()
        
        click.echo(f"Using template: {tmpl.name}")
        
        # Apply template
        engine = TemplateEngine()
        processed_data = engine.apply_template(
            tmpl,
            extracted_data.raw_text,
            extracted_data.tables,
            extracted_data.positioned_text
        )
        
        # Export to UBL
        click.echo("Generating UBL XML...")
        exporter = UBLExporter()
        ubl_xml = exporter.export_to_ubl(processed_data)
        
        # Save output
        if output:
            output_path = Path(output)
        else:
            output_path = Path(pdf_file).with_suffix('.xml')
        
        output_path.write_text(ubl_xml, encoding='utf-8')
        click.echo(f"✅ Saved UBL XML to: {output_path}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True))
@click.option('-t', '--template', help='Template ID to use')
@click.option('-s', '--supplier', help='Supplier hint for auto-detection')
def extract(pdf_file, template, supplier):
    """Extract and preview data from PDF without generating XML."""
    from .extractors.pdf_extractor import PDFExtractor
    from .templates.template_manager import TemplateManager
    from .templates.template_engine import TemplateEngine
    
    try:
        # Extract data
        extractor = PDFExtractor()
        extracted_data = extractor.extract(Path(pdf_file))
        
        # Find template
        manager = TemplateManager()
        if template:
            tmpl = manager.get_template(template)
        else:
            tmpl = manager.find_best_template(extracted_data.raw_text, supplier)
            if not tmpl:
                tmpl = manager.get_default_template()
        
        # Apply template
        engine = TemplateEngine()
        processed_data = engine.apply_template(
            tmpl,
            extracted_data.raw_text,
            extracted_data.tables,
            extracted_data.positioned_text
        )
        
        # Display results
        click.echo(f"\nTemplate Used: {tmpl.name}")
        click.echo(f"Supplier: {processed_data.supplier_name}")
        click.echo(f"Invoice Number: {processed_data.invoice_number}")
        click.echo(f"Date: {processed_data.invoice_date}")
        click.echo(f"Total: {processed_data.currency} {processed_data.total_amount}")
        click.echo(f"\nLine Items: {len(processed_data.line_items)}")
        
        for item in processed_data.line_items[:3]:
            click.echo(f"  - {item['description'][:50]}... @ {item['unit_price']}")
        
        if len(processed_data.line_items) > 3:
            click.echo(f"  ... and {len(processed_data.line_items) - 3} more items")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.group()
def template():
    """Template management commands."""
    pass

@template.command('list')
def template_list():
    """List all available templates."""
    from .templates.template_manager import TemplateManager
    
    manager = TemplateManager()
    templates = manager.list_templates()
    
    if not templates:
        click.echo("No templates found.")
        return
    
    click.echo("\nAvailable Templates:")
    click.echo("-" * 50)
    
    for tmpl in templates:
        click.echo(f"ID: {tmpl.template_id}")
        click.echo(f"Name: {tmpl.name}")
        click.echo(f"Supplier: {tmpl.supplier_name or 'Generic'}")
        click.echo(f"Usage: {tmpl.usage_count} times")
        click.echo("-" * 50)

@template.command('stats')
def template_stats():
    """Show template usage statistics."""
    from .templates.template_manager import TemplateManager
    
    manager = TemplateManager()
    stats = manager.get_stats()
    
    click.echo("\nTemplate Statistics:")
    click.echo(f"Total templates: {stats['total_templates']}")
    click.echo(f"Suppliers with templates: {stats['suppliers_with_templates']}")
    click.echo(f"Average success rate: {stats['average_success_rate']:.1%}")
    
    if stats.get('most_used_template'):
        click.echo(f"Most used: {stats['most_used_template']} ({stats['most_used_template_usage']} times)")

if __name__ == '__main__':
    cli()