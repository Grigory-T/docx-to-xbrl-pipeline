#!/usr/bin/env python3
"""
Emit XBRL Instance

Генерирует валидный XBRL instance файл из канонических фактов.

Usage:
    python scripts/emit_xbrl.py <canonical_facts.json> [--output <report.xbrl>]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List
from lxml import etree
import yaml


class XBRLEmitter:
    """Генерирует XBRL instance документы."""
    
    def __init__(
        self,
        contexts_config: Dict,
        units_config: Dict,
        taxonomy_config: Dict
    ):
        """
        Args:
            contexts_config: Загруженный contexts.yml
            units_config: Загруженный units.yml
            taxonomy_config: Загруженный entrypoints.yml
        """
        self.contexts = contexts_config.get('contexts', {})
        self.units = units_config.get('units', {})
        self.taxonomy = taxonomy_config.get('taxonomy', {})
        self.entrypoint = taxonomy_config.get('entrypoint', {})
        self.namespaces = taxonomy_config.get('namespaces', {})
    
    def emit(self, canonical_facts: List[Dict[str, Any]]) -> etree.Element:
        """
        Генерирует XBRL instance document.
        
        Args:
            canonical_facts: Список канонических фактов
            
        Returns:
            lxml Element для xbrli:xbrl root
        """
        print(f"Emitting XBRL instance with {len(canonical_facts)} fact(s)...")
        
        # Create root element with all namespaces
        nsmap = self.namespaces.copy()
        
        root = etree.Element(
            f"{{{nsmap['xbrli']}}}xbrl",
            nsmap=nsmap
        )
        
        # Add schemaRef
        self._add_schema_ref(root)
        
        # Add contexts
        self._add_contexts(root)
        
        # Add units
        self._add_units(root)
        
        # Add facts
        self._add_facts(root, canonical_facts)
        
        print("[OK] XBRL instance generated")
        
        return root
    
    def _add_schema_ref(self, root: etree.Element):
        """Добавляет link:schemaRef."""
        link_ns = self.namespaces['link']
        xlink_ns = self.namespaces['xlink']
        
        schema_ref = etree.SubElement(
            root,
            f'{{{link_ns}}}schemaRef',
        )
        schema_ref.set(f'{{{xlink_ns}}}type', 'simple')
        schema_ref.set(f'{{{xlink_ns}}}href', self.entrypoint['href'])
        
        print(f"  [OK] Added schemaRef: {self.entrypoint['href']}")
    
    def _add_contexts(self, root: etree.Element):
        """Добавляет все xbrli:context элементы."""
        xbrli_ns = self.namespaces['xbrli']
        
        for ctx_id, ctx_def in self.contexts.items():
            context = etree.SubElement(root, f'{{{xbrli_ns}}}context')
            context.set('id', ctx_def['id'])
            
            # Entity
            entity = etree.SubElement(context, f'{{{xbrli_ns}}}entity')
            identifier = etree.SubElement(entity, f'{{{xbrli_ns}}}identifier')
            identifier.set('scheme', ctx_def['entity']['identifier']['scheme'])
            identifier.text = ctx_def['entity']['identifier']['value']
            
            # Period
            period = etree.SubElement(context, f'{{{xbrli_ns}}}period')
            
            if ctx_def['period']['type'] == 'instant':
                instant = etree.SubElement(period, f'{{{xbrli_ns}}}instant')
                instant.text = ctx_def['period']['instant']
            elif ctx_def['period']['type'] == 'duration':
                start_date = etree.SubElement(period, f'{{{xbrli_ns}}}startDate')
                start_date.text = ctx_def['period']['startDate']
                end_date = etree.SubElement(period, f'{{{xbrli_ns}}}endDate')
                end_date.text = ctx_def['period']['endDate']
        
        print(f"  [OK] Added {len(self.contexts)} context(s)")
    
    def _add_units(self, root: etree.Element):
        """Добавляет все xbrli:unit элементы."""
        xbrli_ns = self.namespaces['xbrli']
        
        for unit_id, unit_def in self.units.items():
            unit = etree.SubElement(root, f'{{{xbrli_ns}}}unit')
            unit.set('id', unit_def['id'])
            
            measure = etree.SubElement(unit, f'{{{xbrli_ns}}}measure')
            measure.text = unit_def['measure']
        
        print(f"  [OK] Added {len(self.units)} unit(s)")
    
    def _add_facts(self, root: etree.Element, canonical_facts: List[Dict[str, Any]]):
        """Добавляет факты."""
        gri_ns = self.namespaces['gri']
        
        for fact in canonical_facts:
            # Parse concept QName (например, "gri:EconomicPerformanceRevenue")
            concept_qname = fact['concept']
            if ':' in concept_qname:
                prefix, local_name = concept_qname.split(':', 1)
                namespace = self.namespaces.get(prefix)
                if not namespace:
                    print(f"  WARNING: Unknown namespace prefix: {prefix}")
                    continue
            else:
                # Default to gri namespace
                namespace = gri_ns
                local_name = concept_qname
            
            # Create fact element
            fact_elem = etree.SubElement(root, f'{{{namespace}}}{local_name}')
            
            # Add attributes
            fact_elem.set('contextRef', fact['contextRef'])
            
            if fact.get('unitRef'):
                fact_elem.set('unitRef', fact['unitRef'])
            
            if fact.get('decimals') is not None:
                fact_elem.set('decimals', str(fact['decimals']))
            
            # Set value
            fact_elem.text = fact['canonicalValue']
            
            print(f"  [OK] Added fact: {fact['factId']} ({concept_qname})")
    
    def save(self, root: etree.Element, output_path: str):
        """
        Сохраняет XBRL instance в файл.
        
        Args:
            root: XBRL root element
            output_path: Путь к выходному файлу
        """
        # Serialize
        xml_str = etree.tostring(
            root,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        )
        
        # Save
        with open(output_path, 'wb') as f:
            f.write(xml_str)
        
        print(f"\n[OK] Saved XBRL instance to: {output_path}")
        print(f"  File size: {Path(output_path).stat().st_size} bytes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate XBRL instance from canonical facts'
    )
    parser.add_argument(
        'canonical_facts',
        help='Path to canonical facts JSON file (from normalize.py)'
    )
    parser.add_argument(
        '--output', '-o',
        default='out/report.xbrl',
        help='Output XBRL file path (default: out/report.xbrl)'
    )
    parser.add_argument(
        '--contexts', '-c',
        default='model/contexts.yml',
        help='Path to contexts.yml (default: model/contexts.yml)'
    )
    parser.add_argument(
        '--units', '-u',
        default='model/units.yml',
        help='Path to units.yml (default: model/units.yml)'
    )
    parser.add_argument(
        '--taxonomy', '-t',
        default='taxonomy/entrypoints.yml',
        help='Path to entrypoints.yml (default: taxonomy/entrypoints.yml)'
    )
    
    args = parser.parse_args()
    
    # Load configs
    print("Loading configuration...")
    
    try:
        with open(args.contexts, 'r', encoding='utf-8') as f:
            contexts_config = yaml.safe_load(f)
        print(f"  [OK] Loaded contexts: {args.contexts}")
    except FileNotFoundError:
        print(f"ERROR: Contexts config not found: {args.contexts}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(args.units, 'r', encoding='utf-8') as f:
            units_config = yaml.safe_load(f)
        print(f"  [OK] Loaded units: {args.units}")
    except FileNotFoundError:
        print(f"ERROR: Units config not found: {args.units}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(args.taxonomy, 'r', encoding='utf-8') as f:
            taxonomy_config = yaml.safe_load(f)
        print(f"  [OK] Loaded taxonomy: {args.taxonomy}")
    except FileNotFoundError:
        print(f"ERROR: Taxonomy config not found: {args.taxonomy}", file=sys.stderr)
        sys.exit(1)
    
    # Load canonical facts
    try:
        with open(args.canonical_facts, 'r', encoding='utf-8') as f:
            canonical_facts = json.load(f)
        print(f"  [OK] Loaded canonical facts: {args.canonical_facts}")
    except FileNotFoundError:
        print(f"ERROR: Canonical facts not found: {args.canonical_facts}", file=sys.stderr)
        sys.exit(1)
    
    print()
    
    # Emit XBRL
    emitter = XBRLEmitter(contexts_config, units_config, taxonomy_config)
    root = emitter.emit(canonical_facts)
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    emitter.save(root, args.output)
    
    print()
    print("=" * 70)
    print("XBRL INSTANCE GENERATED SUCCESSFULLY")
    print("=" * 70)
    print(f"Output: {args.output}")
    print()
    print("Next step: Validate with Arelle")
    print(f"  python scripts/validate_arelle.py {args.output}")
    print("=" * 70)


if __name__ == '__main__':
    main()
