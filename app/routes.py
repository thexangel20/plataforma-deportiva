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

    deportes_filtrados = deportes

    if nivel_costo != "todos":

        deportes_filtrados = [
            deporte
            for deporte in deportes
            if deporte["nivel_costo"] == nivel_costo
        ]

    return render_template(
        "index.html",
        deportes=deportes_filtrados,
        nivel_costo=nivel_costo
    )

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