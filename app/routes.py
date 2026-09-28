from flask import render_template

from app import app


deportes = [
    {
        "nombre": "Fútbol",
        "imagen": "futbol.png",
        "costo": "Bs. 100",
        "tiempo": "90 minutos"
    },
    {
        "nombre": "Baloncesto",
        "imagen": "baloncesto.png",
        "costo": "Bs. 120",
        "tiempo": "90 minutos"
    },
    {
        "nombre": "Natación",
        "imagen": "natacion.png",
        "costo": "Bs. 200",
        "tiempo": "60 minutos"
    },
    {
        "nombre": "Tenis",
        "imagen": "tenis.png",
        "costo": "Bs. 300",
        "tiempo": "120 minutos"
    }
]


@app.route("/")
def inicio():
    return render_template("index.html", deportes=deportes)