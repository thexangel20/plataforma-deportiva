import hmac
from datetime import datetime, timezone

from flask import abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app import app
from app.seguridad import obtener_csrf, requiere_administrador, validar_csrf
from app.servicios import ErrorDatos, consultar

CAMPOS = ('Costos', 'Equipamiento', 'Tiempo de práctica', 'Alimentación',
          'Recomendaciones', 'Condiciones de práctica', 'Imagen', 'Otro')
ESTADOS = ('pendiente', 'revisado')


@app.route('/deportes/<deporte>/reportar', methods=['GET', 'POST'])
def reportar(deporte):
    from app.deportes import obtener_deporte

    campo = request.form.get('campo', '')
    descripcion = request.form.get('descripcion', '').strip()
    estado_http = 200
    if request.method == 'POST':
        validar_csrf()
    try:
        datos_deporte = obtener_deporte(deporte)
    except ErrorDatos as error:
        if request.method != 'POST':
            raise
        flash(str(error), 'error')
        return render_template(
            'reporte.html', nombre=deporte, campos=CAMPOS,
            campo=campo, descripcion=descripcion,
        ), 503
    if request.method == 'POST':
        if campo not in CAMPOS or not 1 <= len(descripcion) <= 1000:
            flash('Selecciona un dato y escribe una descripción de 1 a 1000 caracteres.', 'error')
            estado_http = 400
        else:
            try:
                consultar('reportes_hu4', 'POST', datos={
                    'deporte': deporte, 'campo_observado': campo,
                    'descripcion': descripcion, 'estado': 'pendiente',
                })
                flash('Tu reporte fue enviado correctamente.', 'exito')
                return redirect(url_for('reportar', deporte=deporte))
            except ErrorDatos as error:
                flash(str(error), 'error')
                estado_http = 503
    return render_template('reporte.html', nombre=datos_deporte['nombre'],
                           campos=CAMPOS, campo=campo,
                           descripcion=descripcion), estado_http


@app.route('/admin/ingresar', methods=['GET', 'POST'])
def ingresar():
    if session.get('administrador'):
        return redirect(url_for('listar_reportes'))
    estado_http = 200
    if request.method == 'POST':
        validar_csrf()
        usuario = app.config['ADMIN_USUARIO']
        clave = app.config['ADMIN_PASSWORD_HASH']
        if not usuario or not clave:
            flash('El acceso administrativo todavía no está configurado.', 'error')
            estado_http = 503
        elif (hmac.compare_digest(request.form.get('usuario', '').encode(), usuario.encode())
              and check_password_hash(clave, request.form.get('contrasena', ''))):
            session.clear()
            session['administrador'] = True
            obtener_csrf()
            return redirect(url_for('listar_reportes'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            estado_http = 401
    return render_template('ingresar.html'), estado_http


@app.route('/admin/reportes')
@requiere_administrador
def listar_reportes():
    estado = request.args.get('estado', 'pendiente')
    pagina = request.args.get('pagina', 1, type=int)
    if estado not in (*ESTADOS, 'todos') or pagina is None or pagina < 1:
        abort(400)
    parametros = {'select': '*', 'order': 'fecha_creacion.desc,id.desc',
                  'limit': 51, 'offset': (pagina - 1) * 50}
    if estado != 'todos':
        parametros['estado'] = f'eq.{estado}'
    reportes = []
    estado_http = 200
    try:
        reportes = consultar('reportes_hu4', parametros=parametros)
    except ErrorDatos as error:
        flash(str(error), 'error')
        estado_http = 503
    return render_template('reportes.html', reportes=reportes[:50],
                           siguiente=len(reportes) > 50, pagina=pagina,
                           estado=estado, fallo=estado_http != 200), estado_http


@app.route('/admin/reportes/<int:identificador>/revisar', methods=['POST'])
@requiere_administrador
def revisar_reporte(identificador):
    validar_csrf()
    try:
        resultado = consultar('reportes_hu4', 'PATCH',
            parametros={'id': f'eq.{identificador}', 'estado': 'eq.pendiente'},
            datos={'estado': 'revisado',
                   'fecha_revision': datetime.now(timezone.utc).isoformat()})
        if resultado:
            flash('Reporte marcado como revisado.', 'exito')
        else:
            flash('El reporte no existe o ya fue revisado.', 'error')
    except ErrorDatos as error:
        flash(str(error), 'error')
    return redirect(url_for('listar_reportes'))


@app.route('/admin/salir', methods=['POST'])
@requiere_administrador
def salir():
    validar_csrf()
    session.clear()
    return redirect(url_for('ingresar'))
