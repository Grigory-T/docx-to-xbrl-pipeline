#!/usr/bin/env python3
"""
Normalize Extracted Facts

Нормализует "сырые" значения из DOCX в канонические значения для XBRL,
используя Transformation Registry whitelist.

Usage:
    python scripts/normalize.py <raw_facts.json> [--output <canonical_facts.json>]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class TransformationRegistry:
    """Реализует трансформации из transforms.yml."""
    
    def __init__(self, transforms_config: Dict[str, Any]):
        """
        Args:
            transforms_config: Загруженный transforms.yml
        """
        self.transforms = transforms_config.get('transforms', {})
    
    def transform(self, raw_value: str, transform_name: str) -> str:
        """
        Применяет трансформацию к значению.
        
        Args:
            raw_value: Исходное значение
            transform_name: Название трансформации (например, 'ixt:num-comma-decimal')
            
        Returns:
            Нормализованное значение
            
        Raises:
            ValueError: Если трансформация не найдена или не прошла
        """
        if transform_name not in self.transforms:
            raise ValueError(f"Unknown transformation: {transform_name}")
        
        transform_def = self.transforms[transform_name]
        
        # Применяем трансформацию по имени
        if transform_name == 'ixt:num-dot-decimal':
            return self._num_dot_decimal(raw_value)
        elif transform_name == 'ixt:num-comma-decimal':
            return self._num_comma_decimal(raw_value)
        elif transform_name == 'ixt:num-unit-decimal':
            return self._num_unit_decimal(raw_value)
        elif transform_name == 'ixt:date-day-month-year':
            return self._date_day_month_year(raw_value)
        elif transform_name == 'ixt:date-day-month-year-slash':
            return self._date_day_month_year_slash(raw_value)
        elif transform_name == 'ixt:date-month-day-year':
            return self._date_month_day_year(raw_value)
        elif transform_name == 'ixt:boolean-true':
            return 'true'
        elif transform_name == 'ixt:boolean-false':
            return 'false'
        elif transform_name == 'ixt:normalize-space':
            return self._normalize_space(raw_value)
        else:
            raise ValueError(f"Transformation not implemented: {transform_name}")
    
    # === Numeric transformations ===
    
    def _num_dot_decimal(self, value: str) -> str:
        """1,234.56 → 1234.56"""
        # Удаляем пробелы и запятые (разделители тысяч)
        # Точка остается как decimal separator
        cleaned = value.strip().replace(' ', '').replace(',', '')
        
        # Валидация
        try:
            float(cleaned)
        except ValueError:
            raise ValueError(f"Invalid number format: {value}")
        
        return cleaned
    
    def _num_comma_decimal(self, value: str) -> str:
        """1 234,56 → 1234.56"""
        # Удаляем пробелы и точки (разделители тысяч)
        # Заменяем запятую на точку
        cleaned = value.strip().replace(' ', '').replace('.', '').replace(',', '.')
        
        # Валидация
        try:
            float(cleaned)
        except ValueError:
            raise ValueError(f"Invalid number format: {value}")
        
        return cleaned
    
    def _num_unit_decimal(self, value: str) -> str:
        """1 234,56 EUR → 1234.56"""
        # Удаляем единицу измерения в конце
        match = re.match(r'^([\d\s,\.]+)\s*[A-Z]{3}$', value.strip())
        if not match:
            raise ValueError(f"Invalid unit number format: {value}")
        
        number_part = match.group(1)
        
        # Определяем формат (запятая или точка как decimal separator)
        if ',' in number_part:
            return self._num_comma_decimal(number_part)
        else:
            return self._num_dot_decimal(number_part)
    
    # === Date transformations ===
    
    def _date_day_month_year(self, value: str) -> str:
        """31.12.2025 → 2025-12-31"""
        match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', value.strip())
        if not match:
            raise ValueError(f"Invalid date format (expected DD.MM.YYYY): {value}")
        
        day, month, year = match.groups()
        
        # Валидация
        if not (1 <= int(day) <= 31):
            raise ValueError(f"Invalid day: {day}")
        if not (1 <= int(month) <= 12):
            raise ValueError(f"Invalid month: {month}")
        
        return f"{year}-{month}-{day}"
    
    def _date_day_month_year_slash(self, value: str) -> str:
        """31/12/2025 → 2025-12-31"""
        match = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', value.strip())
        if not match:
            raise ValueError(f"Invalid date format (expected DD/MM/YYYY): {value}")
        
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"
    
    def _date_month_day_year(self, value: str) -> str:
        """12/31/2025 → 2025-12-31"""
        match = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', value.strip())
        if not match:
            raise ValueError(f"Invalid date format (expected MM/DD/YYYY): {value}")
        
        month, day, year = match.groups()
        return f"{year}-{month}-{day}"
    
    # === String transformations ===
    
    def _normalize_space(self, value: str) -> str:
        """Normalize whitespace."""
        return ' '.join(value.split())


class FactNormalizer:
    """Нормализует факты используя registry."""
    
    def __init__(self, facts_config: Dict, transforms_config: Dict):
        """
        Args:
            facts_config: Загруженный facts.yml
            transforms_config: Загруженный transforms.yml
        """
        self.facts_registry = facts_config.get('facts', {})
        self.tr = TransformationRegistry(transforms_config)
    
    def normalize(self, raw_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Нормализует список сырых фактов.
        
        Args:
            raw_facts: Список фактов из extract_docx.py
            
        Returns:
            Список канонических фактов с metadata для XBRL
        """
        canonical_facts = []
        errors = []
        
        print(f"Normalizing {len(raw_facts)} fact(s)...")
        print()
        
        for raw_fact in raw_facts:
            fact_id = raw_fact['factId']
            raw_text = raw_fact['rawText']
            
            # Проверяем что factId есть в registry
            if fact_id not in self.facts_registry:
                error_msg = f"Unknown factId: {fact_id}"
                print(f"  ERROR: {error_msg}")
                errors.append(error_msg)
                continue
            
            fact_def = self.facts_registry[fact_id]
            
            # Применяем трансформацию (если есть)
            transform_name = fact_def.get('transform')
            
            try:
                if transform_name:
                    canonical_value = self.tr.transform(raw_text, transform_name)
                else:
                    # Нет трансформации - просто нормализуем пробелы
                    canonical_value = self.tr._normalize_space(raw_text)
                
                # Создаем канонический факт
                canonical_fact = {
                    'factId': fact_id,
                    'rawValue': raw_text,
                    'canonicalValue': canonical_value,
                    'concept': fact_def['concept'],
                    'type': fact_def['type'],
                    'contextRef': fact_def['contextRef'],
                    'decimals': fact_def.get('decimals'),
                    'unitRef': fact_def.get('unitRef'),
                }
                
                canonical_facts.append(canonical_fact)
                
                print(f"  [OK] {fact_id:30s} '{raw_text}' -> '{canonical_value}'")
                
            except ValueError as e:
                error_msg = f"{fact_id}: {e}"
                print(f"  ERROR: {error_msg}")
                errors.append(error_msg)
                continue
        
        print()
        print("=" * 70)
        print(f"Normalized: {len(canonical_facts)}/{len(raw_facts)} fact(s)")
        
        if errors:
            print(f"Errors: {len(errors)}")
            for error in errors:
                print(f"  - {error}")
            print("=" * 70)
            sys.exit(1)
        
        print("=" * 70)
        
        return canonical_facts


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Normalize extracted facts using Transformation Registry'
    )
    parser.add_argument(
        'raw_facts',
        help='Path to raw facts JSON file (from extract_docx.py)'
    )
    parser.add_argument(
        '--output', '-o',
        default='out/canonical_facts.json',
        help='Output JSON file path (default: out/canonical_facts.json)'
    )
    parser.add_argument(
        '--facts', '-f',
        default='model/facts.yml',
        help='Path to facts.yml (default: model/facts.yml)'
    )
    parser.add_argument(
        '--transforms', '-t',
        default='model/transforms.yml',
        help='Path to transforms.yml (default: model/transforms.yml)'
    )
    
    args = parser.parse_args()
    
    # Load configs
    print("Loading configuration...")
    
    try:
        with open(args.facts, 'r', encoding='utf-8') as f:
            facts_config = yaml.safe_load(f)
        print(f"  [OK] Loaded facts registry: {args.facts}")
    except FileNotFoundError:
        print(f"ERROR: Facts config not found: {args.facts}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(args.transforms, 'r', encoding='utf-8') as f:
            transforms_config = yaml.safe_load(f)
        print(f"  [OK] Loaded transforms registry: {args.transforms}")
    except FileNotFoundError:
        print(f"ERROR: Transforms config not found: {args.transforms}", file=sys.stderr)
        sys.exit(1)
    
    # Load raw facts
    try:
        with open(args.raw_facts, 'r', encoding='utf-8') as f:
            raw_facts = json.load(f)
        print(f"  [OK] Loaded raw facts: {args.raw_facts}")
    except FileNotFoundError:
        print(f"ERROR: Raw facts not found: {args.raw_facts}", file=sys.stderr)
        sys.exit(1)
    
    print()
    
    # Normalize
    normalizer = FactNormalizer(facts_config, transforms_config)
    canonical_facts = normalizer.normalize(raw_facts)
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(canonical_facts, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"[OK] Saved canonical facts to: {output_path}")


if __name__ == '__main__':
    main()
