from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=12
        )
    
    def generate_invoice_pdf(self, invoice_data: dict) -> bytes:
        """Generate PDF invoice."""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            # Title
            title = Paragraph("INVOICE", self.title_style)
            elements.append(title)
            elements.append(Spacer(1, 0.2*inch))
            
            # Invoice details
            details_data = [
                ['Invoice Number:', invoice_data.get('invoice_number', 'N/A')],
                ['Date:', datetime.now().strftime('%B %d, %Y')],
                ['Client:', invoice_data.get('client_name', 'N/A')],
                ['Due Date:', invoice_data.get('due_date', 'N/A')],
                ['Status:', invoice_data.get('status', 'N/A')]
            ]
            
            details_table = Table(details_data, colWidths=[2*inch, 4*inch])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#0f172a')),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(details_table)
            elements.append(Spacer(1, 0.4*inch))
            
            # Items heading
            items_heading = Paragraph("Items", self.heading_style)
            elements.append(items_heading)
            
            # Items table
            items = invoice_data.get('items', [])
            items_data = [['Description', 'Quantity', 'Rate', 'Amount']]
            
            for item in items:
                items_data.append([
                    item.get('description', ''),
                    str(item.get('quantity', 0)),
                    f"₹{item.get('rate', 0):,.2f}",
                    f"₹{item.get('amount', 0):,.2f}"
                ])
            
            items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Totals
            totals_data = [
                ['Subtotal:', f"₹{invoice_data.get('subtotal', 0):,.2f}"],
                ['Tax (18%):', f"₹{invoice_data.get('tax', 0):,.2f}"],
                ['Total:', f"₹{invoice_data.get('total', 0):,.2f}"]
            ]
            
            totals_table = Table(totals_data, colWidths=[5*inch, 2*inch])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (0, 1), colors.HexColor('#64748b')),
                ('TEXTCOLOR', (1, 0), (1, 1), colors.HexColor('#0f172a')),
                ('LINEABOVE', (0, 2), (-1, 2), 2, colors.HexColor('#0f172a')),
                ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#0f172a')),
                ('FONTSIZE', (0, 2), (-1, 2), 14),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(totals_table)
            
            # Build PDF
            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Invoice PDF generated: {invoice_data.get('invoice_number')}")
            return pdf_bytes
        
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise

# Global PDF service instance
pdf_service = PDFService()