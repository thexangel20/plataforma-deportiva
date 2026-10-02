from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def render_pdf(snapshot, fields, cost):
    output = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), title='SportsInfo - Comparación',
                            leftMargin=28, rightMargin=28, topMargin=30, bottomMargin=30)
    p = lambda value: Paragraph(escape(str(value)), styles['BodyText'])
    rows = [[p('Característica')] + [p(s['nombre']) for s in snapshot['sports']]]
    for field, label in fields:
        rows.append([p(label)] + [p(cost(s) if field == 'costo' else str(s[field]) + ' min' if field == 'minutos' else s[field] or 'Por confirmar') for s in snapshot['sports']])
    table = Table(rows, colWidths=[(landscape(A4)[0] - 56) / len(rows[0])] * len(rows[0]), repeatRows=1, splitInRow=1)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e4f1da')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#cad4c6')),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10)]))
    doc.build([Paragraph('SportsInfo · Tu próxima disciplina', styles['Title']),
               Paragraph('Comparación de deportes', styles['Heading1']),
               p('Generada: ' + snapshot['created']), Spacer(1, 16), table,
               Spacer(1, 12), p('Costos orientativos. No se convierten monedas ni se suman períodos distintos.')])
    return output.getvalue()
