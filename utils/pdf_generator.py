from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

def generate_admit_card(data):
    file_name = f"admit_card_{data['reference_number']}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("<b>Admit Card</b>", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Reference No: {data['reference_number']}", styles["Normal"]),
        Spacer(1, 12),
        Table([
            ["Field", "Details"],
            ["Doctor", data["doctor_name"]],
            ["Treatment", data["treatment_name"]],
            ["Date", str(data["appointment_date"])],
            ["Time Slot", data["slot"]]
        ], style=[('GRID', (0,0), (-1,-1), 1, colors.grey)])
    ]
    doc.build(elements)
    return file_name
