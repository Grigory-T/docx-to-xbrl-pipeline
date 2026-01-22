# DOCX to XBRL Pipeline

Automated conversion of Microsoft Word documents with Content Controls to valid XBRL instance files.

## Overview

This project converts `.docx` files containing tagged Content Controls into XBRL instance documents using:

- **Content Controls** (w:sdt) as data source
- **Transformation Registry** for value normalization
- **Arelle** for XBRL validation
- **GRI ESG taxonomy** (simplified)

## Architecture

```
DOCX (Content Controls) 
  → extract_docx.py (parse w:sdt) 
  → normalize.py (Transformation Registry)
  → emit_xbrl.py (generate XBRL)
  → validate_arelle.py (Arelle validation)
  → report.xbrl
```

## Project Structure

```
tagging3/
├── model/           # Registry configurations
│   ├── contexts.yml
│   ├── units.yml
│   ├── facts.yml
│   └── transforms.yml
├── scripts/         # Pipeline scripts
│   ├── extract_docx.py
│   ├── normalize.py
│   ├── emit_xbrl.py
│   ├── validate_arelle.py
│   └── run_pipeline.py
├── tools/           # Utilities
│   └── create_test_docx.py
├── taxonomy/        # Taxonomy config
│   └── entrypoints.yml
└── templates/       # Test DOCX files
    └── report.docx
```

## Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# 1. Create test DOCX with Content Controls
python tools/create_test_docx.py

# 2. Run full pipeline
python scripts/run_pipeline.py templates/report.docx

# Output: out/report.xbrl and out/validation.txt
```

## Individual Steps

```bash
# Extract Content Controls
python scripts/extract_docx.py templates/report.docx

# Normalize values
python scripts/normalize.py out/raw_facts.json

# Generate XBRL
python scripts/emit_xbrl.py out/canonical_facts.json

# Validate XBRL
python scripts/validate_arelle.py out/report.xbrl
```

## Content Controls Setup

1. In Word: Developer → Controls → Rich Text
2. Set Tag property to `factId` (e.g., `revenue_2025`)
3. Enter value inside Content Control (e.g., `1 234 567,89`)

**Example Tags:**
- `revenue_2025` → Revenue 2025 → `1 234 567,89`
- `employees_2025` → Employees 2025 → `250`
- `report_date` → Report Date → `31.12.2025`

## Configuration

### facts.yml - Fact Mapping

Maps factId to XBRL concept with metadata:

```yaml
revenue_2025:
  concept: "gri:EconomicPerformanceRevenue"
  type: monetary
  contextRef: ctx_2025_duration
  unitRef: unit_EUR
  decimals: "0"
  transform: ixt:num-comma-decimal
```

### transforms.yml - Transformations

XBRL Transformation Registry for value normalization:

- **Numbers**: `ixt:num-dot-decimal`, `ixt:num-comma-decimal`
- **Dates**: `ixt:date-day-month-year`
- **Booleans**: `ixt:boolean-true`, `ixt:boolean-false`

## Dependencies

- **lxml** - OOXML/XML parsing
- **PyYAML** - Configuration files
- **arelle-release** - XBRL validation
- **python-docx** - Test DOCX generation

## License

MIT
