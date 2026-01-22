#!/usr/bin/env python3
"""
Extract Content Controls from DOCX

Парсит DOCX файл и извлекает все Content Controls (w:sdt) с их тегами и значениями.
Использует lxml для прямой работы с OOXML, т.к. python-docx плохо поддерживает SDT.

Usage:
    python scripts/extract_docx.py <docx_file> [--output <json_file>]
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import List, Dict, Any
from lxml import etree

# Word OOXML namespaces
NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}


class ContentControlExtractor:
    """Извлекает Content Controls из DOCX файлов."""
    
    def __init__(self, docx_path: str):
        """
        Args:
            docx_path: Путь к DOCX файлу
        """
        self.docx_path = docx_path
        self.facts: List[Dict[str, Any]] = []
    
    def extract(self) -> List[Dict[str, Any]]:
        """
        Извлекает все Content Controls из DOCX.
        
        Returns:
            List of dicts with keys: factId, rawText, position
        """
        print(f"Extracting Content Controls from: {self.docx_path}")
        
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as zf:
                # Читаем word/document.xml
                xml_content = zf.read('word/document.xml')
        except FileNotFoundError:
            print(f"ERROR: File not found: {self.docx_path}", file=sys.stderr)
            sys.exit(1)
        except zipfile.BadZipFile:
            print(f"ERROR: Not a valid DOCX file: {self.docx_path}", file=sys.stderr)
            sys.exit(1)
        except KeyError:
            print(f"ERROR: word/document.xml not found in DOCX", file=sys.stderr)
            sys.exit(1)
        
        # Parse XML
        root = etree.fromstring(xml_content)
        
        # Найти все w:sdt элементы
        sdt_elements = root.xpath('//w:sdt', namespaces=NSMAP)
        
        print(f"Found {len(sdt_elements)} Content Control(s)")
        
        for idx, sdt in enumerate(sdt_elements, 1):
            fact = self._extract_content_control(sdt, idx)
            if fact:
                self.facts.append(fact)
        
        return self.facts
    
    def _extract_content_control(self, sdt: etree.Element, position: int) -> Dict[str, Any]:
        """
        Извлекает данные из одного w:sdt элемента.
        
        Args:
            sdt: w:sdt XML element
            position: Позиция в документе (для диагностики)
            
        Returns:
            Dict с factId, rawText, position или None если нет тега
        """
        # Извлекаем tag (factId)
        tag_elements = sdt.xpath('.//w:sdtPr/w:tag/@w:val', namespaces=NSMAP)
        
        if not tag_elements:
            print(f"  Warning: Content Control #{position} has no tag, skipping")
            return None
        
        fact_id = tag_elements[0]
        
        # Извлекаем текст
        # ВАЖНО: Word часто разбивает текст на множество w:r/w:t элементов
        # Нужно собрать ВСЕ w:t элементы внутри w:sdtContent
        text_parts = sdt.xpath('.//w:sdtContent//w:t/text()', namespaces=NSMAP)
        raw_text = ''.join(text_parts).strip()
        
        # Также проверим w:tab и w:br (пробелы и переносы)
        # Для упрощения заменим их на пробелы
        tabs = sdt.xpath('.//w:sdtContent//w:tab', namespaces=NSMAP)
        if tabs:
            # В реальности нужна более сложная обработка
            pass
        
        print(f"  [{position}] {fact_id:30s} = '{raw_text}'")
        
        return {
            'factId': fact_id,
            'rawText': raw_text,
            'position': position,
        }
    
    def save_json(self, output_path: str):
        """
        Сохраняет извлеченные факты в JSON файл.
        
        Args:
            output_path: Путь к выходному JSON файлу
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.facts, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] Saved {len(self.facts)} fact(s) to: {output_path}")
    
    def print_summary(self):
        """Печатает сводку извлеченных фактов."""
        print("\n" + "=" * 70)
        print("EXTRACTION SUMMARY")
        print("=" * 70)
        print(f"Total Content Controls: {len(self.facts)}")
        print()
        
        if self.facts:
            print("Extracted facts:")
            for fact in self.facts:
                print(f"  {fact['factId']:30s} = {fact['rawText'][:50]}")
        else:
            print("No facts extracted (no Content Controls with tags found)")
        
        print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract Content Controls from DOCX files'
    )
    parser.add_argument(
        'docx_file',
        help='Path to DOCX file'
    )
    parser.add_argument(
        '--output', '-o',
        default='out/raw_facts.json',
        help='Output JSON file path (default: out/raw_facts.json)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Создаем output директорию если нужно
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract
    extractor = ContentControlExtractor(args.docx_file)
    facts = extractor.extract()
    
    # Save
    extractor.save_json(args.output)
    
    # Summary
    extractor.print_summary()
    
    # Exit code
    if facts:
        sys.exit(0)
    else:
        print("\nWARNING: No facts extracted!", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
