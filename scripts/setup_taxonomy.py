#!/usr/bin/env python3
"""
Setup GRI Taxonomy

Extracts GRI taxonomy from zip file to local cache.

Usage:
    python scripts/setup_taxonomy.py
"""

import zipfile
from pathlib import Path
import sys


def extract_taxonomy():
    """Extracts GRI taxonomy from zip file."""
    
    zip_path = Path('gri-sustainability-taxonomy.zip')
    output_path = Path('taxonomy_cache')
    
    if not zip_path.exists():
        print(f"ERROR: {zip_path} not found")
        print()
        print("Please place the GRI taxonomy zip file in the project root.")
        sys.exit(1)
    
    print("=" * 70)
    print("GRI TAXONOMY SETUP")
    print("=" * 70)
    print()
    
    print(f"Extracting: {zip_path}")
    print(f"To:         {output_path}")
    print()
    
    # Remove existing cache
    if output_path.exists():
        print("Removing existing taxonomy cache...")
        import shutil
        shutil.rmtree(output_path)
    
    # Extract
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(output_path)
    
    # Find entry point
    entry_points = list(output_path.rglob('*entry_point*.xsd'))
    
    print(f"[OK] Extracted successfully")
    print()
    print(f"Entry points found: {len(entry_points)}")
    for ep in entry_points:
        rel_path = ep.relative_to(output_path)
        print(f"  - {rel_path}")
    
    print()
    print("=" * 70)
    print("[SUCCESS] GRI TAXONOMY READY")
    print("=" * 70)
    print()
    print("You can now run the pipeline:")
    print("  python scripts/run_pipeline.py templates/report.docx")
    print()


if __name__ == '__main__':
    extract_taxonomy()
