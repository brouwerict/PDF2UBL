#!/usr/bin/env python3
"""Script om XML bestanden lokaal op te slaan vanuit de GUI conversies."""

import json
import requests
from pathlib import Path
import time

def save_completed_conversions(output_dir="./xml_output", api_url="http://localhost:8000"):
    """Download alle voltooide conversies naar een lokale directory."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    try:
        # Haal alle conversie jobs op
        response = requests.get(f"{api_url}/api/conversion/jobs?limit=100")
        if response.status_code != 200:
            print(f"Fout bij ophalen jobs: {response.status_code}")
            return
        
        jobs = response.json()
        completed_jobs = [job for job in jobs if job['status'] == 'completed']
        
        print(f"Gevonden {len(completed_jobs)} voltooide conversies")
        
        for job in completed_jobs:
            job_id = job['job_id']
            filename = job['pdf_filename'].replace('.pdf', '.xml')
            output_file = output_path / filename
            
            # Skip als bestand al bestaat
            if output_file.exists():
                print(f"⏭️  Skip {filename} (bestaat al)")
                continue
            
            try:
                # Download XML
                download_response = requests.get(f"{api_url}/api/conversion/jobs/{job_id}/download")
                if download_response.status_code == 200:
                    output_file.write_text(download_response.text, encoding='utf-8')
                    print(f"✅ Opgeslagen: {filename}")
                else:
                    print(f"❌ Fout bij downloaden {filename}: {download_response.status_code}")
            
            except Exception as e:
                print(f"❌ Fout bij {filename}: {e}")
        
        print(f"\n🎉 Klaar! XML bestanden opgeslagen in: {output_path.absolute()}")
        
    except Exception as e:
        print(f"❌ Fout: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download voltooide XML conversies")
    parser.add_argument("--output", "-o", default="./xml_output", 
                       help="Output directory voor XML bestanden")
    parser.add_argument("--api-url", default="http://localhost:8000", 
                       help="GUI API URL")
    
    args = parser.parse_args()
    
    print("📥 PDF2UBL XML Downloader")
    print("=" * 40)
    save_completed_conversions(args.output, args.api_url)