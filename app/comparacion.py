import re
from datetime import datetime, timezone
from io import BytesIO

from flask import abort, render_template, request, send_file
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app import app
from app.condiciones import resumir_condiciones
from app.deportes import CAMPOS_TEXTO, DEPORTES_INICIALES, obtener_deporte
from app.pdf_comparacion import generar_pdf
from app.seguridad import validar_csrf
from app.servicios import configurado, consultar


def preparar_resumen(deportes):
    resumen = []
    for deporte in deportes:
        costo = deporte.get('costo_estimado')
        costo_texto = 'Información pendiente'
        if costo is not None:
            costo_texto = (
                f"{costo} {deporte.get('moneda') or ''} - "
                f"{deporte.get('periodo_costo') or 'Período pendiente'}"
            )
        campos = [('Costo estimado', costo_texto)]
        campos.extend(resumir_condiciones(deporte))
        campos.extend(
            (etiqueta, deporte.get(campo) or 'Información pendiente')
            for campo, etiqueta in CAMPOS_TEXTO.items()
        )
        resumen.append({'nombre': deporte['nombre'], 'campos': campos})
    return resumen


def firmador_comparacion():
    return URLSafeTimedSerializer(
        app.config['SECRET_KEY'], salt='comparacion-deportes-v1',
    )


@app.route('/comparar')
def comparar():
    seleccion = request.args.getlist('deporte')
    if (len(seleccion) > 3 or len(set(seleccion)) != len(seleccion)
            or any(not re.fullmatch(r'[a-z0-9-]{1,80}', valor)
                   for valor in seleccion)):
        abort(400)
    try:
        pagina = int(request.args.get('pagina', '1'))
        if pagina < 1 or pagina > 100000:
            raise ValueError
    except ValueError:
        abort(400)
    if configurado():
        opciones = consultar('deportes_axel', parametros={
            'select': 'identificador,nombre',
            'order': 'nombre.asc,identificador.asc',
            'limit': 51, 'offset': (pagina - 1) * 50,
        })
    else:
        opciones = list(DEPORTES_INICIALES) if pagina == 1 else []
    siguientes = len(opciones) > 50
    opciones = opciones[:50]
    deportes = [obtener_deporte(valor) for valor in seleccion]
    resumen = preparar_resumen(deportes) if len(deportes) >= 2 else []
    documento = None
    if resumen:
        documento = {
            'deportes': resumen,
            'fecha': datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC'),
            'provisional': not configurado(),
        }
    identificadores_visibles = {opcion['identificador'] for opcion in opciones}
    seleccion_fuera = [
        deporte for deporte in deportes
        if deporte['identificador'] not in identificadores_visibles
    ]
    return render_template(
        'comparacion.html', opciones=opciones, seleccion=seleccion,
        seleccion_fuera=seleccion_fuera, resumen=resumen,
        pagina=pagina, siguiente=siguientes, documento=documento,
        firma=firmador_comparacion().dumps(documento) if documento else '',
        provisional=not configurado(),
    )


@app.route('/comparar/descargar', methods=['POST'])
def descargar_comparacion():
    validar_csrf()
    try:
        documento = firmador_comparacion().loads(
            request.form.get('comparacion', ''), max_age=1800,
        )
    except SignatureExpired:
        return render_template(
            'error.html',
            mensaje='La descarga venció. Vuelve a comparar los deportes.',
        ), 400
    except BadSignature:
        abort(400)
    if not isinstance(documento, dict) or not 2 <= len(
        documento.get('deportes', [])
    ) <= 3:
        abort(400)
    contenido = generar_pdf(documento)
    respuesta = send_file(
        BytesIO(contenido), mimetype='application/pdf', as_attachment=True,
        download_name='comparacion-sportsinfo.pdf', max_age=0,
    )
    respuesta.headers['Cache-Control'] = 'no-store'
    return respuesta
