#!/usr/bin/env python3
"""
Validate XBRL with Arelle

Wrapper для валидации XBRL instance файлов через Arelle.

Usage:
    python scripts/validate_arelle.py <report.xbrl> [--output <validation.txt>]
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


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
        # Try to import Arelle
        try:
            from arelle import Cntlr
            from arelle import ModelManager
            from arelle import FileSource
        except ImportError:
            print("ERROR: Arelle not installed")
            print()
            print("Install Arelle:")
            print("  pip install arelle-release")
            print()
            print("Or run validation manually:")
            print(f"  arelleCmdLine --file {instance_path} --validate")
            print()
            return False
        
        print(f"Instance file: {instance_path}")
        if use_local_taxonomy:
            print(f"Using local taxonomy: taxonomy_cache/")
        print()
        
        # Check file exists
        if not Path(instance_path).exists():
            print(f"ERROR: File not found: {instance_path}")
            return False
        
        print("Initializing Arelle controller...")
        
        # Create controller with logging
        controller = Cntlr.Cntlr(logFileName='logToBuffer')
        
        # Load model
        print("Loading XBRL instance...")
        
        model_xbrl = controller.modelManager.load(instance_path)
        
        if not model_xbrl:
            print("ERROR: Failed to load XBRL instance")
            return False
        
        print(f"[OK] Loaded: {model_xbrl.modelDocument.basename}")
        
        # Display schema references
        if model_xbrl.modelDocument.referencesDocument:
            for ref_doc in model_xbrl.modelDocument.referencesDocument.values():
                if hasattr(ref_doc, 'targetNamespace'):
                    print(f"  Schema: {ref_doc.targetNamespace}")
        
        print()
        
        # Run validation
        print("Running validation...")
        print()
        
        from arelle import Validate
        from arelle import XmlValidate
        
        # Validate XBRL structure
        model_xbrl.modelManager.validate()
        
        # Collect results
        errors = []
        warnings = []
        info = []
        
        for log_entry in controller.logHandler.logRecordBuffer:
            level = log_entry.levelname
            message = log_entry.getMessage()
            
            if level == 'ERROR' or level == 'CRITICAL':
                errors.append(message)
                print(f"  ERROR: {message}")
            elif level == 'WARNING':
                warnings.append(message)
                print(f"  WARNING: {message}")
            elif level == 'INFO':
                info.append(message)
        
        # Results
        print()
        print("=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        print(f"Errors:   {len(errors)}")
        print(f"Warnings: {len(warnings)}")
        print(f"Info:     {len(info)}")
        print()
        
        # Save report
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("XBRL VALIDATION REPORT\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Instance: {instance_path}\n\n")
                
                f.write(f"Errors: {len(errors)}\n")
                for error in errors:
                    f.write(f"  - {error}\n")
                f.write("\n")
                
                f.write(f"Warnings: {len(warnings)}\n")
                for warning in warnings:
                    f.write(f"  - {warning}\n")
                f.write("\n")
                
                f.write(f"Info: {len(info)}\n")
                for i in info:
                    f.write(f"  - {i}\n")
            
            print(f"[OK] Validation report saved to: {output_path}")
            print()
        
        # Close model
        model_xbrl.close()
        
        # Result
        if errors:
            print("[FAILED] VALIDATION FAILED")
            print("=" * 70)
            return False
        else:
            print("[PASSED] VALIDATION PASSED")
            print("=" * 70)
            return True
            
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
