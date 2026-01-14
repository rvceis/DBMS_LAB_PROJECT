"""
Report Export Service
Handles CSV and PDF generation
"""
import os
import csv
import io
from typing import List, Dict
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class ReportExportService:
    """Export reports to CSV and PDF formats"""
    
    def __init__(self, reports_dir: str):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
    
    def export_csv(self, data: List[Dict], fields: List[str], filename: str) -> str:
        """
        Generate CSV file
        
        Args:
            data: List of record dictionaries
            fields: List of field names to include
            filename: Output filename
        
        Returns:
            Full file path
        """
        filepath = os.path.join(self.reports_dir, filename)
        
        # Use all fields if none specified
        if not fields and data:
            fields = list(data[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            for row in data:
                # Convert None to empty string and ensure all values are serializable
                clean_row = {}
                for key in fields:
                    value = row.get(key)
                    if value is None:
                        clean_row[key] = ''
                    elif isinstance(value, (dict, list)):
                        clean_row[key] = str(value)
                    else:
                        clean_row[key] = value
                writer.writerow(clean_row)
        
        return filepath
    
    def export_pdf(self, data: List[Dict], fields: List[str], pdf_config: dict, filename: str) -> str:
        """
        Generate PDF file with formatting
        
        Args:
            data: List of record dictionaries
            fields: List of field names to include
            pdf_config: {
                "title": "Report Title",
                "orientation": "portrait|landscape",
                "page_size": "A4|Letter",
                "show_metadata": True,
                "column_labels": {"field1": "Label 1", ...}
            }
            filename: Output filename
        
        Returns:
            Full file path
        """
        filepath = os.path.join(self.reports_dir, filename)
        
        # PDF setup
        page_size_name = pdf_config.get('page_size', 'A4')
        page_size = A4 if page_size_name == 'A4' else letter
        
        orientation = pdf_config.get('orientation', 'portrait')
        if orientation == 'landscape':
            page_size = landscape(page_size)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=page_size,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        # Prepare table data
        if not fields and data:
            fields = list(data[0].keys())

        num_cols = len(fields)
        # Helper function to wrap text after 3-4 words
        def wrap_text(text, max_words=4):
            if not text or text is None:
                return ''
            text = str(text).strip()
            if not text:
                return ''
            words = text.split()
            if len(words) <= max_words:
                return text
            lines = []
            for i in range(0, len(words), max_words):
                lines.append(' '.join(words[i:i+max_words]))
            return '\n'.join(lines)

        # Get column labels
        column_labels = pdf_config.get('column_labels', {})
        headers = [column_labels.get(f, f.replace('_', ' ').title()) for f in fields]

        if num_cols > 8:
            # Vertical table layout: each record as a 2-column table (Field, Value)
            for idx, row in enumerate(data):
                record_table_data = []
                for i, field in enumerate(fields):
                    label = headers[i]
                    # Try direct, then nested under 'values', then ''
                    value = row.get(field, None)
                    if value is None and isinstance(row.get('values'), dict):
                        value = row['values'].get(field, '')
                    if value is None:
                        value = ''
                    elif isinstance(value, (dict, list)):
                        value = wrap_text(str(value), max_words=3)
                    else:
                        value = wrap_text(str(value), max_words=4)
                    record_table_data.append([label, value])
                record_table = Table(record_table_data, colWidths=[1.8*inch, doc.width-1.8*inch])
                record_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1976d2')),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (0, -1), 9),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('BACKGROUND', (1, 0), (1, -1), colors.white),
                    ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (1, 0), (1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                ]))
                elements.append(Paragraph(f"<b>Record {idx+1}</b>", styles['Heading4']))
                elements.append(record_table)
                elements.append(Spacer(1, 0.18*inch))
        else:
            # Normal horizontal table layout
            table_data = [headers]
            for row in data:
                table_row = []
                for field in fields:
                    value = row.get(field, None)
                    if value is None and isinstance(row.get('values'), dict):
                        value = row['values'].get(field, '')
                    if value is None:
                        value = ''
                    elif isinstance(value, (dict, list)):
                        value = wrap_text(str(value), max_words=3)
                    else:
                        value = wrap_text(str(value), max_words=4)
                    table_row.append(value)
                table_data.append(table_row)
            available_width = doc.width
            min_col_width = 0.8 * inch
            ideal_col_width = available_width / num_cols
            if ideal_col_width < min_col_width:
                ideal_col_width = min_col_width
            col_widths = [ideal_col_width] * num_cols
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            header_fontsize = 10 if num_cols <= 6 else 8 if num_cols <= 10 else 7
            data_fontsize = 9 if num_cols <= 6 else 7 if num_cols <= 10 else 6
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), header_fontsize),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, 0), 'LR'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), data_fontsize),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 1), (-1, -1), 'LR'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table)

        # Footer
        elements.append(Spacer(1, 0.2*inch))
        footer_text = f"<i>End of report - {len(data)} records, {num_cols} fields</i>"
        footer_para = Paragraph(footer_text, styles['Normal'])
        elements.append(footer_para)
        # Build PDF
        doc.build(elements)
        return filepath

    def export_pdf_multi_schema(self, schema_data_list: List[Dict], pdf_config: dict, filename: str) -> str:
        """
        Generate PDF with multiple tables (one per schema)
        
        Args:
            schema_data_list: List of {"schema_name": str, "fields": List[str], "data": List[Dict]}
            pdf_config: PDF configuration
            filename: Output filename
        
        Returns:
            Full file path
        """
        filepath = os.path.join(self.reports_dir, filename)
        
        # PDF setup
        page_size_name = pdf_config.get('page_size', 'A4')
        page_size = A4 if page_size_name == 'A4' else letter
        
        orientation = pdf_config.get('orientation', 'portrait')
        if orientation == 'landscape':
            page_size = landscape(page_size)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=page_size,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=12,
            spaceBefore=12,
        )
        
        # Main title
        title = pdf_config.get('title', 'Report')
        title_para = Paragraph(f"<b>{title}</b>", title_style)
        elements.append(title_para)
        
        # Metadata section
        if pdf_config.get('show_metadata', True):
            total_records = sum(len(s.get('data', [])) for s in schema_data_list)
            meta_text = f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            meta_text += f"<b>Total Records:</b> {total_records}<br/>"
            meta_text += f"<b>Schemas:</b> {len(schema_data_list)}<br/>"
            
            meta_para = Paragraph(meta_text, styles['Normal'])
            elements.append(meta_para)
            elements.append(Spacer(1, 0.3*inch))
        
        # Generate table for each schema
        for schema_info in schema_data_list:
            schema_name = schema_info.get('schema_name', 'Unknown Schema')
            fields = schema_info.get('fields', [])
            data = schema_info.get('data', [])
            
            # Schema section title
            section_para = Paragraph(f"<b>{schema_name}</b> ({len(data)} records)", section_style)
            elements.append(section_para)
            
            if not data:
                elements.append(Paragraph("No records", styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))
                continue
            
            # Helper function to wrap text
            def wrap_text_multi(text, max_words=3):
                """Break text into multiple lines after max_words words"""
                if not text or text is None:
                    return ''
                text = str(text).strip()
                if not text:
                    return ''
                words = text.split()
                if len(words) <= max_words:
                    return text
                lines = []
                for i in range(0, len(words), max_words):
                    lines.append(' '.join(words[i:i+max_words]))
                return '\n'.join(lines)
            
            column_labels = pdf_config.get('column_labels', {})
            headers = ['ID', 'Name', 'Created'] + [column_labels.get(f, f.replace('_', ' ').title()) for f in fields]
            num_cols = len(headers)
            if num_cols > 8:
                # Vertical table layout for each record
                for idx, row in enumerate(data):
                    record_table_data = []
                    # ID, Name, Created
                    record_table_data.append(['ID', str(row.get('id', ''))])
                    record_table_data.append(['Name', str(row.get('name', ''))])
                    record_table_data.append(['Created', str(row.get('created_at', ''))[:10]])
                    for i, field in enumerate(fields):
                        label = headers[i+3]  # offset by 3 for ID, Name, Created
                        value = row.get(field, None)
                        if value is None and isinstance(row.get('values'), dict):
                            value = row['values'].get(field, '')
                        if value is None:
                            value = ''
                        elif isinstance(value, (dict, list)):
                            value = wrap_text_multi(str(value), max_words=2)
                        else:
                            value = wrap_text_multi(str(value), max_words=3)
                        record_table_data.append([label, value])
                    record_table = Table(record_table_data, colWidths=[1.8*inch, doc.width-1.8*inch])
                    record_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1976d2')),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (0, -1), 9),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BACKGROUND', (1, 0), (1, -1), colors.white),
                        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (1, 0), (1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                    ]))
                    elements.append(Paragraph(f"<b>Record {idx+1}</b>", styles['Heading4']))
                    elements.append(record_table)
                    elements.append(Spacer(1, 0.18*inch))
                elements.append(PageBreak())
            else:
                # Normal horizontal table layout
                table_data = [headers]
                for row in data:
                    table_row = [
                        str(row.get('id', '')),
                        wrap_text_multi(str(row.get('name', '')), max_words=2),
                        str(row.get('created_at', ''))[:10]
                    ]
                    for field in fields:
                        value = row.get(field, None)
                        if value is None and isinstance(row.get('values'), dict):
                            value = row['values'].get(field, '')
                        if value is None:
                            value = ''
                        elif isinstance(value, (dict, list)):
                            value = wrap_text_multi(str(value), max_words=2)
                        else:
                            value = wrap_text_multi(str(value), max_words=3)
                        table_row.append(value)
                    table_data.append(table_row)
                available_width = doc.width
                min_col_width = 0.7 * inch
                ideal_col_width = available_width / num_cols
                if ideal_col_width < min_col_width:
                    ideal_col_width = min_col_width
                col_widths = [ideal_col_width] * num_cols
                table = Table(table_data, colWidths=col_widths, repeatRows=1)
                header_fontsize = 8 if num_cols > 8 else 9
                data_fontsize = 6 if num_cols > 8 else 7
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), header_fontsize),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                    ('WORDWRAP', (0, 0), (-1, 0), 'LR'),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), data_fontsize),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                    ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                    ('WORDWRAP', (0, 1), (-1, -1), 'LR'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.4*inch))
                elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        
        return filepath
