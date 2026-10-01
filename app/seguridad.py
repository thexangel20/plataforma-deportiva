import hmac
import secrets
from functools import wraps

from flask import abort, redirect, request, session, url_for

from app import app


def obtener_csrf():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_hex(32)
    return session['csrf']


app.jinja_env.globals['obtener_csrf'] = obtener_csrf


def validar_csrf():
    recibido = request.form.get('csrf', '')
    esperado = session.get('csrf', '')
    if not esperado or not hmac.compare_digest(recibido.encode(), esperado.encode()):
        abort(400, description='El formulario venció. Recarga la página e inténtalo nuevamente.')


def requiere_administrador(funcion):
    @wraps(funcion)
    def protegida(*argumentos, **opciones):
        if not session.get('administrador'):
            return redirect(url_for('ingresar'))
        return funcion(*argumentos, **opciones)
    return protegida
