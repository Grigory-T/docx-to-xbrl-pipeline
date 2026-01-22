#!/usr/bin/env python3
"""
Validate XBRL with Arelle

Wrapper для валидации XBRL instance файлов через Arelle.

Usage:
    python scripts/validate_arelle.py <report.xbrl> [--output <validation.txt>]
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional
import shutil


def validate_with_arelle(
    instance_path: str,
    output_path: Optional[str] = None,
    plugins: Optional[list] = None,
    use_local_taxonomy: bool = True
) -> bool:
    """
    Validates XBRL instance with Arelle.
    
    Args:
        instance_path: Path to XBRL instance file
        output_path: Path for validation report
        plugins: List of Arelle plugins
        use_local_taxonomy: Use local GRI taxonomy cache
        
    Returns:
        True if validation successful, False otherwise
    """
    print("=" * 70)
    print("XBRL VALIDATION with Arelle")
    print("=" * 70)
    print()
    
    try:
        # Try to locate arelleCmdLine CLI
        arelle_cmd = shutil.which("arelleCmdLine")
        if not arelle_cmd:
            candidate = Path(sys.executable).parent / "arelleCmdLine"
            if candidate.exists():
                arelle_cmd = str(candidate)
        if not arelle_cmd:
            print("ERROR: Arelle CLI not found")
            print()
            print("Install Arelle and ensure `arelleCmdLine` is on PATH:")
            print("  pip install arelle-release")
            print()
            print(f"Or run validation manually once installed:")
            print(f"  arelleCmdLine --file {instance_path} --validate")
            return False

        instance_path = str(Path(instance_path))
        instance_abs = Path(instance_path).resolve()
        print(f"Instance file: {instance_abs}")
        if use_local_taxonomy:
            print(f"Using local taxonomy: taxonomy_cache/")
        print()

        # Check file exists
        if not instance_abs.exists():
            print(f"ERROR: File not found: {instance_abs}")
            return False

        # Run Arelle CLI
        cmd = [arelle_cmd, "--file", str(instance_abs), "--validate"]
        print(f"Running: {' '.join(cmd)}")
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        output = proc.stdout or ""
        print(output)

        errors = []
        warnings = []
        info = []
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("[error]") or line.startswith("[fatal]"):
                errors.append(line)
            elif line.startswith("[warning]"):
                warnings.append(line)
            elif line.startswith("[info]"):
                info.append(line)
            elif line.startswith("[message:"):
                warnings.append(line)

        print()
        print("=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        print(f"Errors:   {len(errors)}")
        print(f"Warnings: {len(warnings)}")
        print(f"Info:     {len(info)}")
        print()

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("XBRL VALIDATION REPORT\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Instance: {instance_path}\n\n")
                f.write(output)
            print(f"[OK] Validation report saved to: {output_path}")
            print()

        success = proc.returncode == 0 and not errors
        if success:
            print("[PASSED] VALIDATION PASSED")
            print("=" * 70)
            return True
        else:
            print("[FAILED] VALIDATION FAILED")
            print("=" * 70)
            return False
    except Exception as e:
        print(f"ERROR: Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_basic_xml(instance_path: str) -> bool:
    """
    Базовая валидация XML (если Arelle недоступна).
    
    Args:
        instance_path: Путь к XBRL instance файлу
        
    Returns:
        True если XML валиден, False иначе
    """
    from lxml import etree
    
    print("Running basic XML validation (Arelle not available)...")
    print()
    
    try:
        # Парсим XML
        with open(instance_path, 'rb') as f:
            tree = etree.parse(f)
        
        root = tree.getroot()
        
        print(f"[OK] Valid XML")
        print(f"  Root element: {root.tag}")
        print(f"  Namespaces: {len(root.nsmap)}")
        
        # Подсчет элементов
        contexts = root.xpath('//xbrli:context', namespaces={
            'xbrli': 'http://www.xbrl.org/2003/instance'
        })
        units = root.xpath('//xbrli:unit', namespaces={
            'xbrli': 'http://www.xbrl.org/2003/instance'
        })
        
        print(f"  Contexts: {len(contexts)}")
        print(f"  Units: {len(units)}")
        
        # Подсчет фактов (все элементы кроме служебных)
        all_elements = len(root.xpath('//*'))
        service_elements = len(contexts) + len(units) + 1  # +1 для root
        facts_approx = all_elements - service_elements
        
        print(f"  Facts (approx): {facts_approx}")
        print()
        
        print("=" * 70)
        print("[WARNING] BASIC XML VALIDATION PASSED")
        print("Note: For full XBRL validation, install Arelle:")
        print("  pip install arelle-release")
        print("=" * 70)
        
        return True
        
    except etree.XMLSyntaxError as e:
        print(f"[ERROR] XML SYNTAX ERROR: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] ERROR: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate XBRL instance with Arelle'
    )
    parser.add_argument(
        'instance',
        help='Path to XBRL instance file'
    )
    parser.add_argument(
        '--output', '-o',
        default='out/validation.txt',
        help='Output validation report path (default: out/validation.txt)'
    )
    parser.add_argument(
        '--basic',
        action='store_true',
        help='Use basic XML validation (skip Arelle)'
    )
    
    args = parser.parse_args()
    
    # Создаем output директорию
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Валидация
    if args.basic:
        success = validate_basic_xml(args.instance)
    else:
        success = validate_with_arelle(args.instance, args.output)
        
        # Fallback к базовой валидации если Arelle не установлена
        if not success and "Arelle not installed" in str(success):
            print()
            print("Falling back to basic XML validation...")
            print()
            success = validate_basic_xml(args.instance)
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
