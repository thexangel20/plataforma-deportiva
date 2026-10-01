from flask import render_template
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
    return render_template("index.html", deportes=deportes)

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