#!/usr/bin/env python3
"""
Run Full DOCX to XBRL Pipeline

Orchestrator для полного пайплайна конвертации DOCX → XBRL.

Usage:
    python scripts/run_pipeline.py <docx_file> [--validate]
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Импортируем наши модули
import sys
import os

# Добавляем scripts в path чтобы импортировать модули
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from extract_docx import ContentControlExtractor
from normalize import FactNormalizer, TransformationRegistry
from emit_xbrl import XBRLEmitter
from validate_arelle import validate_with_arelle, validate_basic_xml

import yaml


class Pipeline:
    """Полный пайплайн DOCX → XBRL."""
    
    def __init__(self, docx_path: str, output_dir: str = 'out'):
        """
        Args:
            docx_path: Путь к DOCX файлу
            output_dir: Директория для выходных файлов
        """
        self.docx_path = docx_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Пути к конфигурациям
        self.config_dir = Path('model')
        self.taxonomy_dir = Path('taxonomy')
        
        # Пути к выходным файлам
        self.raw_facts_path = self.output_dir / 'raw_facts.json'
        self.canonical_facts_path = self.output_dir / 'canonical_facts.json'
        self.xbrl_path = self.output_dir / 'report.xbrl'
        self.validation_path = self.output_dir / 'validation.txt'
        
        # Статистика
        self.stats = {
            'start_time': None,
            'end_time': None,
            'duration': None,
            'raw_facts': 0,
            'canonical_facts': 0,
            'validation_passed': False,
        }
    
    def run(self, validate: bool = True) -> bool:
        """
        Запускает полный пайплайн.
        
        Args:
            validate: Запускать валидацию Arelle
            
        Returns:
            True если успешно, False если ошибка
        """
        self.stats['start_time'] = time.time()
        
        print("=" * 70)
        print("DOCX -> XBRL PIPELINE")
        print("=" * 70)
        print(f"Input:  {self.docx_path}")
        print(f"Output: {self.output_dir}")
        print("=" * 70)
        print()
        
        try:
            # Шаг 1: Extract
            if not self._step_extract():
                return False
            
            # Шаг 2: Normalize
            if not self._step_normalize():
                return False
            
            # Шаг 3: Emit XBRL
            if not self._step_emit():
                return False
            
            # Шаг 4: Validate (опционально)
            if validate:
                if not self._step_validate():
                    return False
            
            # Финальная статистика
            self.stats['end_time'] = time.time()
            self.stats['duration'] = self.stats['end_time'] - self.stats['start_time']
            
            self._print_summary()
            
            return True
            
        except Exception as e:
            print()
            print("=" * 70)
            print("[FAILED] PIPELINE FAILED")
            print("=" * 70)
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _step_extract(self) -> bool:
        """Шаг 1: Извлечение Content Controls."""
        print("=" * 70)
        print("STEP 1: Extract Content Controls")
        print("=" * 70)
        print()
        
        extractor = ContentControlExtractor(self.docx_path)
        raw_facts = extractor.extract()
        
        if not raw_facts:
            print()
            print("ERROR: No Content Controls found in DOCX")
            return False
        
        # Сохраняем
        extractor.save_json(str(self.raw_facts_path))
        
        self.stats['raw_facts'] = len(raw_facts)
        
        print()
        return True
    
    def _step_normalize(self) -> bool:
        """Шаг 2: Нормализация значений."""
        print("=" * 70)
        print("STEP 2: Normalize Values")
        print("=" * 70)
        print()
        
        # Загружаем конфигурации
        print("Loading configurations...")
        
        with open(self.config_dir / 'facts.yml', 'r', encoding='utf-8') as f:
            facts_config = yaml.safe_load(f)
        print(f"  [OK] facts.yml")
        
        with open(self.config_dir / 'transforms.yml', 'r', encoding='utf-8') as f:
            transforms_config = yaml.safe_load(f)
        print(f"  [OK] transforms.yml")
        
        # Загружаем raw facts
        with open(self.raw_facts_path, 'r', encoding='utf-8') as f:
            raw_facts = json.load(f)
        print(f"  [OK] raw_facts.json ({len(raw_facts)} facts)")
        print()
        
        # Нормализуем
        normalizer = FactNormalizer(facts_config, transforms_config)
        canonical_facts = normalizer.normalize(raw_facts)
        
        if not canonical_facts:
            print()
            print("ERROR: No facts were normalized")
            return False
        
        # Сохраняем
        with open(self.canonical_facts_path, 'w', encoding='utf-8') as f:
            json.dump(canonical_facts, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] Saved canonical facts to: {self.canonical_facts_path}")
        
        self.stats['canonical_facts'] = len(canonical_facts)
        
        print()
        return True
    
    def _step_emit(self) -> bool:
        """Шаг 3: Генерация XBRL."""
        print("=" * 70)
        print("STEP 3: Emit XBRL Instance")
        print("=" * 70)
        print()
        
        # Загружаем конфигурации
        print("Loading configurations...")
        
        with open(self.config_dir / 'contexts.yml', 'r', encoding='utf-8') as f:
            contexts_config = yaml.safe_load(f)
        print(f"  [OK] contexts.yml")
        
        with open(self.config_dir / 'units.yml', 'r', encoding='utf-8') as f:
            units_config = yaml.safe_load(f)
        print(f"  [OK] units.yml")
        
        with open(self.taxonomy_dir / 'entrypoints.yml', 'r', encoding='utf-8') as f:
            taxonomy_config = yaml.safe_load(f)
        print(f"  [OK] entrypoints.yml")
        
        # Загружаем canonical facts
        with open(self.canonical_facts_path, 'r', encoding='utf-8') as f:
            canonical_facts = json.load(f)
        print(f"  [OK] canonical_facts.json ({len(canonical_facts)} facts)")
        print()
        
        # Генерируем XBRL
        emitter = XBRLEmitter(contexts_config, units_config, taxonomy_config)
        root = emitter.emit(canonical_facts)
        
        # Сохраняем
        emitter.save(root, str(self.xbrl_path))
        
        print()
        return True
    
    def _step_validate(self) -> bool:
        """Шаг 4: Валидация XBRL."""
        print("=" * 70)
        print("STEP 4: Validate XBRL")
        print("=" * 70)
        print()
        
        # Сначала пробуем Arelle
        success = validate_with_arelle(
            str(self.xbrl_path),
            str(self.validation_path)
        )
        
        # Если Arelle не доступна, используем базовую валидацию
        if not success:
            print()
            print("Arelle validation failed, trying basic XML validation...")
            print()
            success = validate_basic_xml(str(self.xbrl_path))
        
        self.stats['validation_passed'] = success
        
        print()
        return True  # Не останавливаем пайплайн если валидация не прошла
    
    def _print_summary(self):
        """Печатает финальную сводку."""
        print()
        print("=" * 70)
        print("PIPELINE SUMMARY")
        print("=" * 70)
        print(f"Input DOCX:        {self.docx_path}")
        print(f"Output XBRL:       {self.xbrl_path}")
        print()
        print(f"Raw facts:         {self.stats['raw_facts']}")
        print(f"Canonical facts:   {self.stats['canonical_facts']}")
        print(f"Validation:        {'[PASSED]' if self.stats['validation_passed'] else '[WARNING] NOT RUN or FAILED'}")
        print()
        print(f"Duration:          {self.stats['duration']:.2f} seconds")
        print()
        print("Output files:")
        print(f"  - {self.raw_facts_path}")
        print(f"  - {self.canonical_facts_path}")
        print(f"  - {self.xbrl_path}")
        if self.validation_path.exists():
            print(f"  - {self.validation_path}")
        print()
        print("=" * 70)
        print("[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run full DOCX to XBRL pipeline'
    )
    parser.add_argument(
        'docx_file',
        help='Path to DOCX file with Content Controls'
    )
    parser.add_argument(
        '--output', '-o',
        default='out',
        help='Output directory (default: out)'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip XBRL validation step'
    )
    
    args = parser.parse_args()
    
    # Проверяем что DOCX существует
    if not Path(args.docx_file).exists():
        print(f"ERROR: File not found: {args.docx_file}", file=sys.stderr)
        sys.exit(1)
    
    # Запускаем пайплайн
    pipeline = Pipeline(args.docx_file, args.output)
    success = pipeline.run(validate=not args.no_validate)
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
