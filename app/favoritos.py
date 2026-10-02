import re

from flask import abort, flash, redirect, render_template, session, url_for
from werkzeug.exceptions import NotFound

from app import app
from app.deportes import obtener_deporte
from app.seguridad import validar_csrf
from app.servicios import ErrorDatos


def identificadores_favoritos():
    return session.get('favoritos_demostracion', [])


app.jinja_env.globals['identificadores_favoritos'] = identificadores_favoritos


@app.route('/favoritos')
def listar_favoritos():
    deportes = []
    fallo = False
    for identificador in identificadores_favoritos():
        try:
            deportes.append(obtener_deporte(identificador))
        except (NotFound, ErrorDatos) as error:
            fallo = fallo or isinstance(error, ErrorDatos)
            deportes.append({
                'identificador': identificador, 'nombre': identificador,
                'no_disponible': True,
            })
    if fallo:
        flash('No se pudieron consultar algunos deportes. '
              'Tu selección se conserva; inténtalo nuevamente.', 'error')
    return render_template('favoritos.html', deportes=deportes), (
        503 if fallo else 200
    )


@app.route('/favoritos/<identificador>/agregar', methods=['POST'])
def agregar_favorito(identificador):
    validar_csrf()
    deporte = obtener_deporte(identificador)
    favoritos = list(identificadores_favoritos())
    if identificador in favoritos:
        flash('Este deporte ya está en tus favoritos de demostración.', 'exito')
    elif len(favoritos) >= 20:
        flash('La demostración admite hasta 20 favoritos. '
              'Quita uno antes de agregar otro.', 'error')
    else:
        favoritos.append(identificador)
        session['favoritos_demostracion'] = favoritos
        flash(f"{deporte['nombre']} se agregó a tus favoritos de demostración.",
              'exito')
    return redirect(url_for('listar_favoritos'))


@app.route('/favoritos/<identificador>/quitar', methods=['POST'])
def quitar_favorito(identificador):
    validar_csrf()
    if not re.fullmatch(r'[a-z0-9-]{1,80}', identificador):
        abort(404)
    favoritos = list(identificadores_favoritos())
    if identificador in favoritos:
        favoritos.remove(identificador)
        session['favoritos_demostracion'] = favoritos
        flash('Deporte eliminado de tus favoritos de demostración.', 'exito')
    else:
        flash('Ese deporte ya no está en tu lista.', 'error')
    return redirect(url_for('listar_favoritos'))
