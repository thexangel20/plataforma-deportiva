from flask import flash, render_template, request, abort

from app import app
from app.servicios import ErrorDatos, configurado, consultar


@app.route('/')
def inicio():
    from app.deportes import DEPORTES_INICIALES

    pagina = request.args.get('pagina', 1, type=int)
    if pagina is None or pagina < 1:
        abort(400)
    deportes = list(DEPORTES_INICIALES) if pagina == 1 else []
    estado_http = 200
    siguiente = False
    if configurado():
        try:
            deportes = consultar('deportes_axel', parametros={
                'select': '*', 'order': 'nombre.asc,identificador.asc',
                'limit': 51, 'offset': (pagina - 1) * 50})
            siguiente = len(deportes) > 50
            deportes = deportes[:50]
        except ErrorDatos as error:
            flash(str(error), 'error')
            deportes = []
            estado_http = 503
    return render_template('index.html', deportes=deportes, pagina=pagina,
                           siguiente=siguiente, provisional=not configurado()), estado_http
