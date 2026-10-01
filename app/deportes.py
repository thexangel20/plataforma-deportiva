import re
import warnings
from decimal import Decimal, InvalidOperation
from io import BytesIO
from urllib.parse import quote
from uuid import uuid4

from flask import abort, flash, redirect, render_template, request, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

from app import app
from app.condiciones import OPCIONES_CONDICIONES, validar_condiciones
from app.seguridad import requiere_administrador, validar_csrf
from app.servicios import ErrorDatos, configurado, consultar, solicitar

DEPORTES_INICIALES = (
    {'identificador': 'futbol', 'nombre': 'Fútbol'},
    {'identificador': 'baloncesto', 'nombre': 'Baloncesto'},
    {'identificador': 'natacion', 'nombre': 'Natación'},
    {'identificador': 'tenis', 'nombre': 'Tenis'},
)
CAMPOS_TEXTO = {
    'equipamiento': 'Equipamiento',
    'tiempo_practica': 'Tiempo y frecuencia de práctica',
    'alimentacion': 'Alimentación',
    'recomendaciones': 'Recomendaciones',
    'condiciones': 'Condiciones de práctica',
}


def obtener_deporte(identificador):
    if not re.fullmatch(r'[a-z0-9-]{1,80}', identificador):
        abort(404)
    if configurado():
        registros = consultar('deportes_axel', parametros={
            'select': '*', 'identificador': f'eq.{identificador}', 'limit': 1})
    else:
        registros = [dict(deporte) for deporte in DEPORTES_INICIALES
                     if deporte['identificador'] == identificador]
    if not registros:
        abort(404)
    return registros[0]


def direccion_imagen(ruta):
    if not ruta:
        return None
    bucket = quote(app.config['SUPABASE_BUCKET'], safe='')
    return (app.config['SUPABASE_URL'] + '/storage/v1/object/public/'
            + bucket + '/' + quote(ruta, safe='/'))


app.jinja_env.globals['direccion_imagen'] = direccion_imagen


@app.errorhandler(ErrorDatos)
def error_datos(error):
    return render_template('error.html', mensaje=str(error)), 503


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(413)
def error_solicitud(error):
    mensajes = {400: 'La solicitud no es válida. Vuelve al formulario e inténtalo nuevamente.',
                404: 'No se encontró la página o el deporte solicitado.',
                413: 'El archivo es demasiado grande. Selecciona una imagen de hasta 5 MB.'}
    return render_template('error.html', mensaje=mensajes[error.code]), error.code


@app.route('/deportes/<identificador>')
def detalle_deporte(identificador):
    deporte = obtener_deporte(identificador)
    return render_template('detalle_deporte.html', deporte=deporte,
                           campos=CAMPOS_TEXTO, provisional=not configurado())


@app.route('/admin/deportes')
@requiere_administrador
def administrar_deportes():
    pagina = request.args.get('pagina', 1, type=int)
    if pagina is None or pagina < 1:
        abort(400)
    deportes = consultar('deportes_axel', parametros={
        'select': '*', 'order': 'nombre.asc,identificador.asc',
        'limit': 51, 'offset': (pagina - 1) * 50})
    return render_template('administrar_deportes.html', deportes=deportes[:50],
                           pagina=pagina, siguiente=len(deportes) > 50)


def validar_datos(formulario):
    datos = {'nombre': formulario.get('nombre', '').strip(),
             'moneda': formulario.get('moneda', '').strip().upper(),
             'periodo_costo': formulario.get('periodo_costo', '').strip()}
    if not 1 <= len(datos['nombre']) <= 100:
        raise ValueError('El nombre debe tener entre 1 y 100 caracteres.')
    if not re.fullmatch(r'[A-Z]{3}', datos['moneda']):
        raise ValueError('Escribe una moneda de tres letras, por ejemplo BOB.')
    if len(datos['periodo_costo']) > 100:
        raise ValueError('El período del costo debe tener como máximo 100 caracteres.')
    costo = formulario.get('costo_estimado', '').strip()
    datos['costo_estimado'] = None
    if costo:
        try:
            valor = Decimal(costo)
            if (not valor.is_finite() or valor < 0 or valor > Decimal('99999999.99')
                    or valor != valor.quantize(Decimal('0.01'))):
                raise InvalidOperation
        except InvalidOperation:
            raise ValueError('El costo debe ser positivo o cero, con hasta dos decimales.') from None
        if not datos['periodo_costo']:
            raise ValueError('Indica a qué período corresponde el costo.')
        datos['costo_estimado'] = str(valor)
    for campo in CAMPOS_TEXTO:
        texto = formulario.get(campo, '').strip()
        if len(texto) > 3000:
            raise ValueError(f'{CAMPOS_TEXTO[campo]} admite hasta 3000 caracteres.')
        datos[campo] = texto
    datos.update(validar_condiciones(formulario))
    return datos


def preparar_imagen(archivo):
    contenido = archivo.read(5 * 1024 * 1024 + 1)
    if len(contenido) > 5 * 1024 * 1024:
        raise ValueError('La imagen debe pesar como máximo 5 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(contenido)) as imagen:
                if imagen.format not in ('JPEG', 'PNG', 'WEBP'):
                    raise ValueError('Selecciona una imagen JPEG, PNG o WebP.')
                if imagen.width * imagen.height > 16000000:
                    raise ValueError('La imagen debe tener como máximo 16 millones de píxeles.')
                imagen.load()
                salida = BytesIO()
                imagen = ImageOps.exif_transpose(imagen)
                imagen.convert('RGB').save(salida, format='JPEG', quality=85)
                resultado = salida.getvalue()
                if len(resultado) > 5 * 1024 * 1024:
                    raise ValueError('La imagen procesada supera los 5 MB. Reduce su tamaño.')
                return resultado
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning):
        raise ValueError('El archivo no es una imagen válida.') from None


def subir_imagen(contenido):
    ruta = f'deportes/{uuid4().hex}.jpg'
    bucket = quote(app.config['SUPABASE_BUCKET'], safe='')
    solicitar(f'/storage/v1/object/{bucket}/{ruta}', 'POST',
              datos=contenido, tipo='image/jpeg')
    return ruta


def descartar_imagen(ruta, identificador):
    bucket = quote(app.config['SUPABASE_BUCKET'], safe='')
    try:
        registros = consultar('deportes_axel', parametros={
            'select': 'imagen_ruta',
            'identificador': f'eq.{identificador}', 'limit': 1})
        if registros and registros[0].get('imagen_ruta') == ruta:
            return
        solicitar(f'/storage/v1/object/{bucket}', 'DELETE', datos={'prefixes': [ruta]})
    except ErrorDatos:
        app.logger.warning('No se pudo limpiar una imagen de una actualización fallida.')


@app.route('/admin/deportes/<identificador>/editar', methods=['GET', 'POST'])
@requiere_administrador
def editar_deporte(identificador):
    if not configurado():
        raise ErrorDatos('Configura Supabase y ejecuta el SQL antes de editar deportes.')
    if request.method == 'POST':
        validar_csrf()
    try:
        deporte = obtener_deporte(identificador)
    except ErrorDatos as error:
        if request.method != 'POST':
            raise
        flash(str(error), 'error')
        flash('Si elegiste una imagen, selecciónala nuevamente.', 'error')
        deporte = {
            campo: request.form.get(campo, '')
            for campo in ('nombre', 'moneda', 'periodo_costo',
                          'costo_estimado', *CAMPOS_TEXTO,
                          *OPCIONES_CONDICIONES)
        }
        deporte['identificador'] = identificador
        return render_template(
            'editar_deporte.html', deporte=deporte, campos=CAMPOS_TEXTO,
        ), 503
    estado_http = 200
    if request.method == 'POST':
        nueva_imagen = None
        try:
            datos = validar_datos(request.form)
            archivo = request.files.get('imagen')
            if archivo and archivo.filename:
                nueva_imagen = subir_imagen(preparar_imagen(archivo))
                datos['imagen_ruta'] = nueva_imagen
            resultado = consultar('deportes_axel', 'PATCH',
                parametros={'identificador': f'eq.{identificador}'}, datos=datos)
            if not resultado:
                raise ErrorDatos('El deporte ya no existe. No se guardaron los cambios.')
            flash('Los cambios del deporte fueron guardados.', 'exito')
            return redirect(url_for('detalle_deporte', identificador=identificador))
        except (ValueError, ErrorDatos) as error:
            if nueva_imagen:
                descartar_imagen(nueva_imagen, identificador)
            flash(str(error), 'error')
            estado_http = 400 if isinstance(error, ValueError) else 503
            if request.files.get('imagen'):
                flash('Selecciona nuevamente la imagen antes de reintentar.', 'error')
            for campo in ('nombre', 'moneda', 'periodo_costo',
                          'costo_estimado', *CAMPOS_TEXTO,
                          *OPCIONES_CONDICIONES):
                deporte[campo] = request.form.get(campo, '')
    return render_template('editar_deporte.html', deporte=deporte,
                           campos=CAMPOS_TEXTO), estado_http
