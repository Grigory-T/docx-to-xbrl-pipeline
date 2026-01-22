#!/usr/bin/env python3
"""
Create Test DOCX with Content Controls

Программно создает DOCX файл с Content Controls (w:sdt) через прямую
манипуляцию OOXML структурой. Это необходимо для тестирования парсинга
Content Controls.
"""

import os
import sys
import zipfile
from pathlib import Path
from lxml import etree

# Word OOXML namespaces
NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
}

# Shortcuts
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def create_content_control(fact_id: str, text_value: str) -> etree.Element:
    """
    Создает w:sdt (Content Control) элемент с тегом и значением.
    
    Args:
        fact_id: Идентификатор факта (сохраняется в w:tag)
        text_value: Текстовое значение Content Control
        
    Returns:
        lxml Element для w:sdt
    """
    # w:sdt
    sdt = etree.Element(f'{W}sdt', nsmap=NSMAP)
    
    # w:sdtPr (properties)
    sdt_pr = etree.SubElement(sdt, f'{W}sdtPr')
    
    # w:tag с factId
    tag = etree.SubElement(sdt_pr, f'{W}tag')
    tag.set(f'{W}val', fact_id)
    
    # w:id (уникальный ID для Word UI)
    sdt_id = etree.SubElement(sdt_pr, f'{W}id')
    sdt_id.set(f'{W}val', str(hash(fact_id) % 100000000))
    
    # w:placeholder
    placeholder = etree.SubElement(sdt_pr, f'{W}placeholder')
    doc_part = etree.SubElement(placeholder, f'{W}docPart')
    doc_part.set(f'{W}val', 'DefaultPlaceholder_1081868574')
    
    # w:showingPlcHdr (не показывать placeholder)
    showing = etree.SubElement(sdt_pr, f'{W}showingPlcHdr')
    showing.set(f'{W}val', '0')
    
    # w:text (указывает что это текстовый Content Control)
    text_ctrl = etree.SubElement(sdt_pr, f'{W}text')
    
    # w:sdtContent (actual content)
    sdt_content = etree.SubElement(sdt, f'{W}sdtContent')
    
    # w:p (paragraph)
    p = etree.SubElement(sdt_content, f'{W}p')
    
    # w:r (run)
    r = etree.SubElement(p, f'{W}r')
    
    # w:t (text)
    t = etree.SubElement(r, f'{W}t')
    t.text = text_value
    
    return sdt


def create_paragraph(text: str, bold: bool = False, size: int = 24) -> etree.Element:
    """
    Создает обычный параграф (без Content Control).
    
    Args:
        text: Текст параграфа
        bold: Жирный шрифт
        size: Размер шрифта (в half-points, 24 = 12pt)
    """
    p = etree.Element(f'{W}p', nsmap=NSMAP)
    
    # w:pPr (paragraph properties)
    p_pr = etree.SubElement(p, f'{W}pPr')
    spacing = etree.SubElement(p_pr, f'{W}spacing')
    spacing.set(f'{W}after', '200')
    
    # w:r (run)
    r = etree.SubElement(p, f'{W}r')
    
    # w:rPr (run properties)
    r_pr = etree.SubElement(r, f'{W}rPr')
    
    if bold:
        b = etree.SubElement(r_pr, f'{W}b')
    
    sz = etree.SubElement(r_pr, f'{W}sz')
    sz.set(f'{W}val', str(size))
    
    # w:t (text)
    t = etree.SubElement(r, f'{W}t')
    t.text = text
    
    return p


def create_heading(text: str, level: int = 1) -> etree.Element:
    """Создает заголовок."""
    p = etree.Element(f'{W}p', nsmap=NSMAP)
    
    # w:pPr
    p_pr = etree.SubElement(p, f'{W}pPr')
    p_style = etree.SubElement(p_pr, f'{W}pStyle')
    p_style.set(f'{W}val', f'Heading{level}')
    
    # w:r
    r = etree.SubElement(p, f'{W}r')
    
    # w:t
    t = etree.SubElement(r, f'{W}t')
    t.text = text
    
    return p


def create_document_xml() -> bytes:
    """Создает word/document.xml с тестовыми Content Controls."""
    
    # Root element
    root = etree.Element(
        f'{W}document',
        nsmap=NSMAP
    )
    
    # w:body
    body = etree.SubElement(root, f'{W}body')
    
    # === Заголовок документа ===
    body.append(create_heading('ESG Sustainability Report 2025', level=1))
    body.append(create_paragraph(''))
    
    # === Секция: Company Information ===
    body.append(create_heading('Company Information', level=2))
    
    body.append(create_paragraph('Company Name:', bold=True))
    body.append(create_content_control('company_name', 'Test Company LLC'))
    body.append(create_paragraph(''))
    
    body.append(create_paragraph('Report Date:', bold=True))
    body.append(create_content_control('report_date', '31.12.2025'))
    body.append(create_paragraph(''))
    
    # === Секция: Economic Performance ===
    body.append(create_heading('Economic Performance', level=2))
    
    body.append(create_paragraph('Revenue 2025 (EUR):', bold=True))
    body.append(create_content_control('revenue_2025', '1 234 567,89'))
    body.append(create_paragraph(''))
    
    body.append(create_paragraph('Revenue 2024 (EUR):', bold=True))
    body.append(create_content_control('revenue_2024', '987 654,32'))
    body.append(create_paragraph(''))
    
    body.append(create_paragraph('Operating Costs 2025 (EUR):', bold=True))
    body.append(create_content_control('operating_costs_2025', '876 543,21'))
    body.append(create_paragraph(''))
    
    body.append(create_paragraph('Net Profit 2025 (EUR):', bold=True))
    body.append(create_content_control('net_profit_2025', '358 024,68'))
    body.append(create_paragraph(''))
    
    # === Секция: Social Indicators ===
    body.append(create_heading('Social Indicators', level=2))
    
    body.append(create_paragraph('Total Employees (end of 2025):', bold=True))
    body.append(create_content_control('employees_2025', '250'))
    body.append(create_paragraph(''))
    
    body.append(create_paragraph('Total Employees (end of 2024):', bold=True))
    body.append(create_content_control('employees_2024', '235'))
    body.append(create_paragraph(''))
    
    body.append(create_paragraph('Female Employees (end of 2025):', bold=True))
    body.append(create_content_control('employees_female_2025', '127'))
    body.append(create_paragraph(''))
    
    # === Секция: Environmental Indicators ===
    body.append(create_heading('Environmental Indicators', level=2))
    
    body.append(create_paragraph('Energy Consumption 2025 (GJ):', bold=True))
    body.append(create_content_control('energy_consumption_2025', '12 345,67'))
    body.append(create_paragraph(''))
    
    body.append(create_paragraph('CO2 Emissions 2025 (tonnes):', bold=True))
    body.append(create_content_control('co2_emissions_2025', '1 234,56'))
    body.append(create_paragraph(''))
    
    # w:sectPr (section properties) - обязателен в конце body
    sect_pr = etree.SubElement(body, f'{W}sectPr')
    pg_sz = etree.SubElement(sect_pr, f'{W}pgSz')
    pg_sz.set(f'{W}w', '11906')
    pg_sz.set(f'{W}h', '16838')
    
    # Serialize to XML
    xml_str = etree.tostring(
        root,
        encoding='UTF-8',
        xml_declaration=True,
        standalone=True,
        pretty_print=True
    )
    
    return xml_str


def create_rels_xml() -> bytes:
    """Создает word/_rels/document.xml.rels."""
    RELS_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
    
    root = etree.Element(
        f'{{{RELS_NS}}}Relationships',
        nsmap={None: RELS_NS}
    )
    
    # Relationship to styles
    rel = etree.SubElement(root, f'{{{RELS_NS}}}Relationship')
    rel.set('Id', 'rId1')
    rel.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles')
    rel.set('Target', 'styles.xml')
    
    return etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True)


def create_content_types_xml() -> bytes:
    """Создает [Content_Types].xml."""
    CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'
    
    root = etree.Element(
        f'{{{CT_NS}}}Types',
        nsmap={None: CT_NS}
    )
    
    # Default types
    for ext, content_type in [
        ('rels', 'application/vnd.openxmlformats-package.relationships+xml'),
        ('xml', 'application/xml'),
    ]:
        default = etree.SubElement(root, f'{{{CT_NS}}}Default')
        default.set('Extension', ext)
        default.set('ContentType', content_type)
    
    # Override for document.xml
    override = etree.SubElement(root, f'{{{CT_NS}}}Override')
    override.set('PartName', '/word/document.xml')
    override.set('ContentType', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml')
    
    # Override for styles.xml
    override = etree.SubElement(root, f'{{{CT_NS}}}Override')
    override.set('PartName', '/word/styles.xml')
    override.set('ContentType', 'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml')
    
    return etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True)


def create_styles_xml() -> bytes:
    """Создает минимальный word/styles.xml."""
    root = etree.Element(f'{W}styles', nsmap=NSMAP)
    
    # Default document defaults
    doc_defaults = etree.SubElement(root, f'{W}docDefaults')
    
    # Normal style
    style = etree.SubElement(root, f'{W}style')
    style.set(f'{W}type', 'paragraph')
    style.set(f'{W}styleId', 'Normal')
    
    name = etree.SubElement(style, f'{W}name')
    name.set(f'{W}val', 'Normal')
    
    # Heading 1
    style_h1 = etree.SubElement(root, f'{W}style')
    style_h1.set(f'{W}type', 'paragraph')
    style_h1.set(f'{W}styleId', 'Heading1')
    
    name_h1 = etree.SubElement(style_h1, f'{W}name')
    name_h1.set(f'{W}val', 'Heading 1')
    
    # Heading 2
    style_h2 = etree.SubElement(root, f'{W}style')
    style_h2.set(f'{W}type', 'paragraph')
    style_h2.set(f'{W}styleId', 'Heading2')
    
    name_h2 = etree.SubElement(style_h2, f'{W}name')
    name_h2.set(f'{W}val', 'Heading 2')
    
    return etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True)


def create_docx(output_path: str):
    """
    Создает полный DOCX файл с Content Controls.
    
    Args:
        output_path: Путь для сохранения DOCX файла
    """
    print(f"Creating test DOCX with Content Controls...")
    
    # Create ZIP (DOCX is just a ZIP)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as docx:
        # [Content_Types].xml
        docx.writestr('[Content_Types].xml', create_content_types_xml())
        
        # word/document.xml
        docx.writestr('word/document.xml', create_document_xml())
        
        # word/styles.xml
        docx.writestr('word/styles.xml', create_styles_xml())
        
        # word/_rels/document.xml.rels
        docx.writestr('word/_rels/document.xml.rels', create_rels_xml())
        
        # _rels/.rels (package relationships)
        rels_ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
        root = etree.Element(f'{{{rels_ns}}}Relationships', nsmap={None: rels_ns})
        rel = etree.SubElement(root, f'{{{rels_ns}}}Relationship')
        rel.set('Id', 'rId1')
        rel.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument')
        rel.set('Target', 'word/document.xml')
        
        docx.writestr('_rels/.rels', etree.tostring(root, encoding='UTF-8', xml_declaration=True))
    
    print(f"[OK] Created: {output_path}")
    print(f"  File size: {os.path.getsize(output_path)} bytes")
    
    # Список Content Controls для проверки
    print("\nContent Controls created:")
    controls = [
        ('company_name', 'Test Company LLC'),
        ('report_date', '31.12.2025'),
        ('revenue_2025', '1 234 567,89'),
        ('revenue_2024', '987 654,32'),
        ('operating_costs_2025', '876 543,21'),
        ('net_profit_2025', '358 024,68'),
        ('employees_2025', '250'),
        ('employees_2024', '235'),
        ('employees_female_2025', '127'),
        ('energy_consumption_2025', '12 345,67'),
        ('co2_emissions_2025', '1 234,56'),
    ]
    
    for fact_id, value in controls:
        print(f"  - {fact_id:30s} = {value}")
    
    print(f"\n[OK] Total: {len(controls)} Content Controls")


def main():
    """Main entry point."""
    # Определяем путь к выходному файлу
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'templates'
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / 'report.docx'
    
    print("=" * 70)
    print("DOCX Test File Generator")
    print("=" * 70)
    print()
    
    create_docx(str(output_path))
    
    print()
    print("=" * 70)
    print("Next steps:")
    print("  1. Open the file in Microsoft Word to verify Content Controls")
    print("  2. Run: python scripts/extract_docx.py templates/report.docx")
    print("=" * 70)


if __name__ == '__main__':
    main()
