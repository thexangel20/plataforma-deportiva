import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from app import app


class ErrorDatos(Exception):
    pass


def configurado():
    return bool(app.config['SUPABASE_URL'] and app.config['SUPABASE_SECRET_KEY'])


def solicitar(ruta, metodo='GET', parametros=None, datos=None, tipo='application/json'):
    direccion = app.config['SUPABASE_URL']
    clave = app.config['SUPABASE_SECRET_KEY']
    if urlparse(direccion).scheme != 'https' or not clave:
        raise ErrorDatos('Falta configurar la conexión a Supabase en el servidor.')
    cabeceras = {'apikey': clave, 'Content-Type': tipo}
    if not clave.startswith('sb_secret_'):
        cabeceras['Authorization'] = f'Bearer {clave}'
    if ruta.startswith('/rest/'):
        cabeceras['Prefer'] = 'return=representation'
    cuerpo = datos
    if datos is not None and not isinstance(datos, bytes):
        cuerpo = json.dumps(datos).encode('utf-8')
    consulta = '?' + urlencode(parametros) if parametros else ''
    solicitud = Request(direccion + ruta + consulta, data=cuerpo,
                        headers=cabeceras, method=metodo)
    try:
        with urlopen(solicitud, timeout=15) as respuesta:
            contenido = respuesta.read()
        return json.loads(contenido) if contenido else None
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        raise ErrorDatos('No se pudo completar la operación en Supabase. Inténtalo nuevamente.') from None


def consultar(tabla, metodo='GET', parametros=None, datos=None):
    resultado = solicitar('/rest/v1/' + tabla, metodo, parametros, datos)
    if not isinstance(resultado, list):
        raise ErrorDatos('La base de datos devolvió una respuesta inesperada.')
    return resultado
