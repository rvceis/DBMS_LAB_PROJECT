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
        
        # Title
        title = pdf_config.get('title', 'Report')
        title_para = Paragraph(f"<b>{title}</b>", title_style)
        elements.append(title_para)
        
        # Metadata section
        if pdf_config.get('show_metadata', True):
            meta_text = f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            meta_text += f"<b>Total Records:</b> {len(data)}<br/>"
            
            # Add filter info if available
            if pdf_config.get('filters'):
                meta_text += f"<b>Filters Applied:</b> {len(pdf_config['filters'])}<br/>"
            
            meta_para = Paragraph(meta_text, styles['Normal'])
            elements.append(meta_para)
            elements.append(Spacer(1, 0.3*inch))
        
        # Prepare table data
        if not fields and data:
            fields = list(data[0].keys())
        
        # Get column labels
        column_labels = pdf_config.get('column_labels', {})
        headers = [column_labels.get(f, f.replace('_', ' ').title()) for f in fields]
        
        table_data = [headers]  # Header row
        
        for row in data:
            table_row = []
            for field in fields:
                value = row.get(field, '')
                if value is None:
                    value = ''
                elif isinstance(value, (dict, list)):
                    value = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                else:
                    value = str(value)
                    if len(value) > 50:
                        value = value[:47] + '...'
                table_row.append(value)
            table_data.append(table_row)
        
        # Calculate column widths
        available_width = doc.width
        num_cols = len(fields)
        col_width = available_width / num_cols
        col_widths = [col_width] * num_cols
        
        # Create table
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Table style
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Footer
        elements.append(Spacer(1, 0.3*inch))
        footer_text = f"<i>End of report - {len(data)} records</i>"
        footer_para = Paragraph(footer_text, styles['Normal'])
        elements.append(footer_para)
        
        # Build PDF
        doc.build(elements)
        
        return filepath
