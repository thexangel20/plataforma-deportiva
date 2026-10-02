from flask import render_template, request
from app import app


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/planificador", methods=["GET", "POST"])
def planificador():
    resultado = None

    if request.method == "POST":
        # Aquí irá la lógica (T4-T8)
        # Por ahora solo guardamos los datos del formulario
        resultado = {
            "nivel": request.form.get("nivel"),
            "objetivo": request.form.get("objetivo"),
            "dias": request.form.get("dias"),
            "horas": request.form.get("horas"),
        }

    return render_template("planificador.html", resultado=resultado)