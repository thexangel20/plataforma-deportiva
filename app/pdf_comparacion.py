from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)


def texto_seguro(valor):
    texto = ''.join(
        caracter for caracter in str(valor)
        if caracter in '\n\t' or ord(caracter) >= 32
    )
    return escape(texto).replace('\n', '<br/>')


def generar_pdf(documento):
    salida = BytesIO()
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(
        'CuerpoDeporte', fontName='Helvetica', fontSize=10.5,
        leading=15, spaceAfter=10, alignment=TA_LEFT,
        splitLongWords=True,
    ))
    estilos.add(ParagraphStyle(
        'EtiquetaDeporte', parent=estilos['Heading3'],
        textColor=colors.HexColor('#1d4ed8'), spaceBefore=12,
    ))
    estilos.add(ParagraphStyle(
        'CeldaDeporte', parent=estilos['CuerpoDeporte'],
        fontSize=9, leading=12, spaceAfter=0,
    ))
    elementos = [
        Paragraph('SportsInfo', estilos['Title']),
        Paragraph('Comparación de deportes', estilos['Heading1']),
        Paragraph(texto_seguro(documento['fecha']), estilos['Normal']),
        Spacer(1, 8 * mm),
        Paragraph(
            'Resumen de los deportes seleccionados. Los costos se muestran '
            'con su moneda y período; no se convierten ni se suman.',
            estilos['CuerpoDeporte'],
        ),
    ]
    if documento.get('provisional'):
        elementos.append(Paragraph(
            'Catálogo inicial: faltan datos de la base de datos. '
            'La información desconocida se indica como pendiente.',
            estilos['CuerpoDeporte'],
        ))
    deportes = documento['deportes']
    filas = [[Paragraph('Característica', estilos['CeldaDeporte'])] + [
        Paragraph(texto_seguro(deporte['nombre']), estilos['CeldaDeporte'])
        for deporte in deportes
    ]]
    for indice in range(4):
        filas.append([
            Paragraph(texto_seguro(deportes[0]['campos'][indice][0]),
                      estilos['CeldaDeporte'])
        ] + [
            Paragraph(texto_seguro(deporte['campos'][indice][1]),
                      estilos['CeldaDeporte'])
            for deporte in deportes
        ])
    ancho = 174 * mm
    tabla = Table(
        filas, colWidths=[ancho / (len(deportes) + 1)] * (len(deportes) + 1),
        repeatRows=1, hAlign='LEFT',
    )
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eaf2ff')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
    ]))
    elementos.append(tabla)
    for deporte in deportes:
        elementos.extend([
            PageBreak(),
            Paragraph(texto_seguro(deporte['nombre']), estilos['Heading1']),
        ])
        for etiqueta, valor in deporte['campos']:
            elementos.extend([
                Paragraph(texto_seguro(etiqueta), estilos['EtiquetaDeporte']),
                Paragraph(texto_seguro(valor), estilos['CuerpoDeporte']),
            ])

    def pie_pagina(lienzo, pagina):
        lienzo.saveState()
        lienzo.setFont('Helvetica', 9)
        lienzo.setFillColor(colors.HexColor('#475569'))
        lienzo.drawString(18 * mm, 12 * mm, 'SportsInfo - Comparación')
        lienzo.drawRightString(192 * mm, 12 * mm, str(pagina.page))
        lienzo.restoreState()

    documento_pdf = SimpleDocTemplate(
        salida, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=22 * mm,
        title='Comparación de deportes | SportsInfo', author='SportsInfo',
    )
    documento_pdf.build(
        elementos, onFirstPage=pie_pagina, onLaterPages=pie_pagina,
    )
    return salida.getvalue()
