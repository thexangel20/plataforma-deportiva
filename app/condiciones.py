from app import app

OPCIONES_CONDICIONES = {
    'espacio_practica': {
        '': 'Información pendiente',
        'interior': 'Interiores',
        'exterior': 'Exteriores',
        'ambos': 'Interiores y exteriores',
    },
    'instalaciones_especiales': {
        '': 'Información pendiente', 'si': 'Sí', 'no': 'No',
    },
    'requiere_companeros': {
        '': 'Información pendiente', 'si': 'Sí', 'no': 'No',
    },
}
ETIQUETAS_CONDICIONES = {
    'espacio_practica': 'Espacio de práctica',
    'instalaciones_especiales': '¿Necesita instalaciones especiales?',
    'requiere_companeros': '¿Requiere compañeros?',
}


def resumir_condiciones(deporte):
    return [
        (ETIQUETAS_CONDICIONES[campo],
         opciones.get(deporte.get(campo) or '', 'Información pendiente'))
        for campo, opciones in OPCIONES_CONDICIONES.items()
    ]


def validar_condiciones(formulario):
    datos = {}
    for campo, opciones in OPCIONES_CONDICIONES.items():
        valor = formulario.get(campo, '')
        if valor not in opciones:
            raise ValueError('Selecciona una opción válida para las condiciones.')
        datos[campo] = valor or None
    return datos


app.jinja_env.globals.update(
    resumir_condiciones=resumir_condiciones,
    opciones_condiciones=OPCIONES_CONDICIONES,
    etiquetas_condiciones=ETIQUETAS_CONDICIONES,
)
