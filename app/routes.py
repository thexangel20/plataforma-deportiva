from flask import flash, render_template, request, abort

from app import app
from app.servicios import ErrorDatos, configurado, consultar


@app.route('/')
def inicio():
    from app.deportes import DEPORTES_INICIALES, adaptar_deporte

    pagina = request.args.get('pagina', 1, type=int)
    if pagina is None or pagina < 1:
        abort(400)
    deportes = [adaptar_deporte(deporte) for deporte in DEPORTES_INICIALES] if pagina == 1 else []
    estado_http = 200
    siguiente = False
    if configurado():
        try:
            deportes = consultar('sportsinfo_deportes', parametros={
                'select': '*', 'order': 'nombre.asc,id.asc',
                'limit': 51, 'offset': (pagina - 1) * 50})
            siguiente = len(deportes) > 50
            deportes = [adaptar_deporte(deporte) for deporte in deportes[:50]]
        except ErrorDatos as error:
            flash(str(error), 'error')
            deportes = []
            estado_http = 503
    return render_template('index.html', deportes=deportes, pagina=pagina,
                           siguiente=siguiente, provisional=not configurado()), estado_http
