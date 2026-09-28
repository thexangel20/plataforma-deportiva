from flask import render_template

from app import app


deportes = [
    {
        "nombre": "Fútbol",
        "imagen": "futbol.jpg",
        "costo": "Bs. 150",
        "tiempo": "90 minutos"
    },
    {
        "nombre": "Baloncesto",
        "imagen": "baloncesto.jpg",
        "costo": "Bs. 120",
        "tiempo": "90 minutos"
    },
    {
        "nombre": "Natación",
        "imagen": "natacion.jpg",
        "costo": "Bs. 200",
        "tiempo": "60 minutos"
    },
    {
        "nombre": "Tenis",
        "imagen": "tenis.jpg",
        "costo": "Bs. 300",
        "tiempo": "120 minutos"
    }
]


@app.route("/")
def inicio():
    return render_template("index.html", deportes=deportes)