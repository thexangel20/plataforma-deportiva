from flask import render_template, request, session
from app import app
from app.datos_deportes import datos_deportes


def convertir_altura(valor):
    if not valor:
        return None

    valor = valor.strip().lower().replace(",", ".")

    if valor.endswith("cm"):
        valor = valor.replace("cm", "").strip()
        return float(valor) / 100

    if valor.endswith("m"):
        valor = valor.replace("m", "").strip()
        return float(valor)

    numero = float(valor)

    if numero >= 100:
        return numero / 100

    return numero



@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/comparacion", methods=["GET", "POST"])
def comparacion():

    deportes = [
        "Fútbol",
        "Baloncesto",
        "Natación",
        "Tenis"
    ]

    deporte1 = None
    deporte2 = None
    informacion1 = None
    informacion2 = None
    error = None
    comparacion_resultado = None

    if request.method == "POST":

        deporte1 = request.form.get("deporte1")
        deporte2 = request.form.get("deporte2")

        if not deporte1 or not deporte2:

            error = "Debes seleccionar dos deportes."

        elif deporte1 == deporte2:

            error = "Debes seleccionar dos deportes diferentes."

        else:

            informacion1 = datos_deportes.get(deporte1)
            informacion2 = datos_deportes.get(deporte2)

            if informacion1 and informacion2:

                comparacion_resultado = {
                    "deporte1": informacion1,
                    "deporte2": informacion2
                }

            else:

                error = "No se encontró la información de uno de los deportes."

    return render_template(
        "comparacion.html",
        deportes=deportes,
        deporte1=deporte1,
        deporte2=deporte2,
        informacion1=informacion1,
        informacion2=informacion2,
        comparacion=comparacion_resultado,
        error=error
    )


@app.route("/perfil", methods=["GET", "POST"])
def perfil():

    perfil_usuario = session.get("perfil")
    mensaje = None
    error = None

    if request.method == "POST":

        try:

            edad = int(request.form.get("edad"))
            peso = float(request.form.get("peso"))
            altura = int(request.form.get("altura"))
            dias_disponibles = int(
                request.form.get("dias_disponibles")
            )
            horas_disponibles = float(
                request.form.get("horas_disponibles")
            )
            presupuesto = float(
                request.form.get("presupuesto")
            )

            sexo = request.form.get("sexo")
            experiencia = request.form.get("experiencia")
            objetivo = request.form.get("objetivo")
            deportes_practicados = request.form.get(
                "deportes_practicados"
            )

            if edad < 5 or edad > 100:
                raise ValueError("La edad debe estar entre 5 y 100 años.")

            if peso <= 0:
                raise ValueError("El peso debe ser mayor a cero.")

            if altura <= 0:
                raise ValueError("La altura debe ser mayor a cero.")

            if dias_disponibles < 1 or dias_disponibles > 7:
                raise ValueError(
                    "Los días disponibles deben estar entre 1 y 7."
                )

            if horas_disponibles <= 0:
                raise ValueError(
                    "Las horas disponibles deben ser mayores a cero."
                )

            if presupuesto < 0:
                raise ValueError(
                    "El presupuesto no puede ser negativo."
                )

            perfil_usuario = {
                "edad": edad,
                "sexo": sexo,
                "peso": peso,
                "altura": altura,
                "experiencia": experiencia,
                "objetivo": objetivo,
                "deportes_practicados": deportes_practicados,
                "dias_disponibles": dias_disponibles,
                "horas_disponibles": horas_disponibles,
                "presupuesto": presupuesto
            }

            session["perfil"] = perfil_usuario

            mensaje = "Tu perfil se guardó correctamente."

        except (TypeError, ValueError) as error_validacion:

            error = str(error_validacion)

    return render_template(
        "perfil.html",
        perfil=perfil_usuario,
        mensaje=mensaje,
        error=error
    )