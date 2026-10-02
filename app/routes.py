from flask import render_template, request
import unicodedata
from app import app

def normalizar_texto(texto):

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return texto.lower()

deportes = [
    {
        "nombre": "Fútbol",
        "palabras_clave": [
            "futbol",
            "fútbol",
            "pelota",
            "balon",
            "balón",
            "cancha",
            "resistencia"
        ],
        "imagen": "futbol.png",
        "costo": "Bs. 150",
        "nivel_costo": "Bajo",
        "inversion_inicial": "Bs. 150 - Bs. 450",
        "costo_recurrente": "Bs. 5 - Bs. 15 por persona/partido",
        "tiempo": "90 minutos",
        "dieta": "Se recomienda mantener una alimentación equilibrada que incluya carbohidratos, proteínas, frutas y verduras, además de una hidratación adecuada.",
        "recomendaciones": [
            "Comenzar los entrenamientos de manera progresiva.",
            "Realizar un calentamiento antes de practicar.",
            "Utilizar calzado y equipamiento adecuados.",
            "Mantener una hidratación adecuada durante la actividad."
        ]
    },
    {
        "nombre": "Baloncesto",
        "palabras_clave": [
            "baloncesto",
            "basquet",
            "básquet",
            "pelota",
            "balon",
            "balón",
            "cancha",
            "salto",
            "resistencia"
        ],
        "imagen": "baloncesto.png",
        "costo": "Bs. 120",
        "nivel_costo": "Medio",
        "inversion_inicial": "Bs. 300 - Bs. 800",
        "costo_recurrente": "Costos recurrentes moderados",
        "tiempo": "90 minutos",
        "dieta": "Se recomienda una alimentación equilibrada con suficiente energía, proteínas, frutas y verduras, acompañada de una buena hidratación.",
        "recomendaciones": [
            "Realizar un calentamiento antes de comenzar.",
            "Iniciar con ejercicios de intensidad moderada.",
            "Utilizar calzado deportivo adecuado.",
            "Mantener una hidratación adecuada."
        ]
    },
    {
        "nombre": "Natación",
        "palabras_clave": [
            "natacion",
            "natación",
            "agua",
            "piscina",
            "nadar",
            "resistencia"
        ],
        "imagen": "natacion.png",
        "costo": "Bs. 200",
        "nivel_costo": "Medio",
        "inversion_inicial": "Bs. 200 - Bs. 500",
        "costo_recurrente": "Bs. 150 - Bs. 400 mensuales",
        "tiempo": "60 minutos",
        "dieta": "Se recomienda una alimentación equilibrada que aporte energía y proteínas, junto con una hidratación adecuada antes y después de la práctica.",
        "recomendaciones": [
            "Comenzar con sesiones de intensidad moderada.",
            "Realizar ejercicios de calentamiento.",
            "Utilizar el equipamiento adecuado para la piscina.",
            "Mantener una hidratación adecuada."
        ]
    },
    {
        "nombre": "Tenis",
        "palabras_clave": [
            "tenis",
            "raqueta",
            "pelota",
            "cancha",
            "coordinacion",
            "coordinación",
            "resistencia"
        ],
        "imagen": "tenis.png",
        "costo": "Bs. 180",
        "nivel_costo": "Alto",
        "inversion_inicial": "Bs. 600 - Bs. 1.800+",
        "costo_recurrente": "Bs. 40 - Bs. 100 por hora de cancha",
        "tiempo": "60 minutos",
        "dieta": "Se recomienda una alimentación equilibrada que incluya fuentes de energía, proteínas, frutas y verduras, además de una hidratación adecuada.",
        "recomendaciones": [
            "Comenzar con sesiones de intensidad moderada.",
            "Realizar un calentamiento antes de jugar.",
            "Utilizar calzado y equipamiento adecuados.",
            "Mantener una hidratación adecuada."
        ]
    }
]

@app.route("/")
def inicio():

    nivel_costo = request.args.get("nivel_costo", "todos")
    busqueda = request.args.get("busqueda", "").strip()

    deportes_filtrados = deportes

    if nivel_costo != "todos":

        deportes_filtrados = [
            deporte
            for deporte in deportes_filtrados
            if deporte["nivel_costo"] == nivel_costo
        ]

    if busqueda:

        busqueda_normalizada = normalizar_texto(busqueda)

        deportes_filtrados = [
            deporte
            for deporte in deportes_filtrados
            if busqueda_normalizada in normalizar_texto(deporte["nombre"])
            or any(
                busqueda_normalizada in normalizar_texto(palabra)
                for palabra in deporte["palabras_clave"]
            )
        ]

    return render_template(
        "index.html",
        deportes=deportes_filtrados,
        nivel_costo=nivel_costo,
        busqueda=busqueda
    )

@app.route("/registro", methods=["GET", "POST"])
def registrar_deporte():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        presupuesto = request.form.get("presupuesto", "").strip()
        tiempo = request.form.get("tiempo", "").strip()
        dieta = request.form.get("dieta", "").strip()
        recomendaciones = request.form.get("recomendaciones", "").strip()

        imagen = request.files.get("imagen")

        errores = []

        if not nombre:
            errores.append("El nombre del deporte es obligatorio.")

        if not presupuesto:
            errores.append("El presupuesto es obligatorio.")

        if not tiempo:
            errores.append("El tiempo recomendado es obligatorio.")

        if not dieta:
            errores.append("La dieta sugerida es obligatoria.")

        if not recomendaciones:
            errores.append("Las recomendaciones son obligatorias.")

        if not imagen or imagen.filename == "":
            errores.append("La imagen del deporte es obligatoria.")

        if errores:
            return "<br>".join(errores), 400

        return "Datos válidos correctamente"

    return render_template("registro_deporte.html")

@app.route("/us2/deporte/<nombre>")
def detalle_us2(nombre):

    deporte_encontrado = None

    for deporte in deportes:

        if normalizar_texto(deporte["nombre"]) == normalizar_texto(nombre):
            deporte_encontrado = deporte
            break

    if deporte_encontrado is None:
        return "Deporte no encontrado", 404

    return render_template(
        "detalle_us2.html",
        deporte=deporte_encontrado
    )