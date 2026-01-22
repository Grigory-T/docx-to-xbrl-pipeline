# DOCX to XBRL Pipeline

Converts Microsoft Word documents with Content Controls to valid XBRL files using the official GRI Sustainability Taxonomy.

## Features

- Extracts Content Controls from DOCX files
- Normalizes values using XBRL Transformation Registry
- Generates valid XBRL with real GRI taxonomy concepts
- Validates output with Arelle

## Installation

```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Extract GRI taxonomy (the repo already includes `gri-sustainability-taxonomy.zip`)
python scripts/setup_taxonomy.py
```

## Usage

```bash
# Create test DOCX
python tools/create_test_docx.py

# Run pipeline
python scripts/run_pipeline.py templates/report.docx

# Output: out/report.xbrl
 
# Validate with Arelle CLI (invoked automatically by the pipeline as well)
python scripts/validate_arelle.py out/report.xbrl --output out/validation.txt
```

## Taxonomy

The repository now ships with `gri-sustainability-taxonomy.zip`. Run `python scripts/setup_taxonomy.py` once to extract it into `taxonomy_cache/`; both `scripts/run_pipeline.py` and Arelle will resolve the schema to the extracted `entry_point_2025-06-23.xsd`.

## Content Controls Setup

1. In Word: Developer → Controls → Rich Text
2. Set Tag property (e.g., `revenue_2025`)
3. Enter value (e.g., `1 234 567,89`)

## Supported GRI Concepts

- `gri:RevenuesGeneratedFromDirectEconomicValue` - Revenue
- `gri:EconomicValueDistributed` - Operating costs
- `gri:EconomicValueRetained` - Net profit
- `gri:TotalNumberOfEmployees` - Employees
- `gri:TotalEnergyConsumptionWithinOrganization` - Energy
- `gri:GrossDirectScope1GHGEmissions` - GHG emissions

## Configuration

Edit `model/facts.yml` to map Content Control tags to GRI concepts:

```yaml
revenue_2025:
  concept: "gri:RevenuesGeneratedFromDirectEconomicValue"
  type: monetary
  contextRef: ctx_2025_duration
  unitRef: unit_EUR
  decimals: "0"
  transform: ixt:num-comma-decimal
```

Edit `model/transforms.yml` for value transformations:
- Numbers: `ixt:num-dot-decimal`, `ixt:num-comma-decimal`
- Dates: `ixt:date-day-month-year`
- Booleans: `ixt:boolean-true`, `ixt:boolean-false`

## License

MIT
