#!/usr/bin/env python3
"""Extract text from Fixxar PDF using OCR."""

import sys
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

def extract_with_ocr(pdf_path):
    """Extract text using OCR from PDF."""
    print(f"🔍 Extracting text from: {pdf_path}")
    
    # Convert PDF to image using PyMuPDF
    doc = fitz.open(pdf_path)
    
    all_text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Convert page to image
        pix = page.get_pixmap()
        img_data = pix.tobytes("ppm")
        
        # Convert to PIL Image
        img = Image.open(io.BytesIO(img_data))
        
        # Use OCR to extract text
        text = pytesseract.image_to_string(img, lang='nld')
        all_text += text + "\n"
        
        print(f"Page {page_num + 1} text:")
        print("-" * 40)
        print(text)
        print("-" * 40)
    
    doc.close()
    return all_text

def extract_simple(pdf_path):
    """Simple extraction without OCR."""
    print(f"🔍 Simple extraction from: {pdf_path}")
    
    # Try PyMuPDF first
    doc = fitz.open(pdf_path)
    all_text = ""
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        all_text += text + "\n"
        print(f"Page {page_num + 1} text (PyMuPDF):")
        print("-" * 40)
        print(repr(text))  # Show raw representation
        print("-" * 40)
    
    doc.close()
    return all_text

if __name__ == "__main__":
    pdf_file = Path("tests/fixxar 15-05-2025.pdf")
    
    if not pdf_file.exists():
        print(f"❌ PDF file not found: {pdf_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("TRYING SIMPLE EXTRACTION FIRST")
    print("=" * 60)
    
    simple_text = extract_simple(pdf_file)
    
    if simple_text.strip():
        print("✅ Simple extraction successful!")
        print(f"Extracted text length: {len(simple_text)}")
    else:
        print("❌ Simple extraction failed, trying OCR...")
        
        try:
            import io
            ocr_text = extract_with_ocr(pdf_file)
            print("✅ OCR extraction successful!")
            print(f"Extracted text length: {len(ocr_text)}")
            
            # Save OCR text for analysis
            with open("fixxar_ocr_text.txt", "w", encoding="utf-8") as f:
                f.write(ocr_text)
            print("💾 OCR text saved to fixxar_ocr_text.txt")
            
        except ImportError:
            print("❌ pytesseract not available")
        except Exception as e:
            print(f"❌ OCR extraction failed: {e}")