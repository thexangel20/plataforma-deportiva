from app.datos_deportes import datos_deportes


def calcular_recomendacion(
    edad,
    experiencia,
    objetivo,
    disponibilidad,
    presupuesto
):
    resultados = []

    for nombre, deporte in datos_deportes.items():

        puntaje = 0
        motivos = []

        if objetivo == "resistencia":
            if nombre in ["Running", "Ciclismo", "Natación", "Fútbol"]:
                puntaje += 4
                motivos.append(
                    "se relaciona con tu objetivo de resistencia"
                )

        elif objetivo == "fuerza":
            if nombre in ["Boxeo", "Artes Marciales", "Baloncesto"]:
                puntaje += 4
                motivos.append(
                    "puede contribuir al desarrollo de fuerza"
                )

        elif objetivo == "flexibilidad":
            if nombre == "Yoga":
                puntaje += 4
                motivos.append(
                    "está relacionado con flexibilidad y movilidad"
                )

        elif objetivo == "perder_peso":
            if nombre in ["Running", "Natación", "Ciclismo", "Boxeo"]:
                puntaje += 4
                motivos.append(
                    "implica actividad física cardiovascular"
                )

        if experiencia == "principiante":
            if deporte["dificultad"] == "Básica":
                puntaje += 3
                motivos.append("presenta una dificultad básica")

            elif deporte["dificultad"] == "Intermedia":
                puntaje += 1

        elif experiencia == "intermedio":
            if deporte["dificultad"] == "Intermedia":
                puntaje += 3
                motivos.append(
                    "su dificultad coincide con tu experiencia"
                )

        elif experiencia == "avanzado":
            if deporte["dificultad"] == "Alta":
                puntaje += 3
                motivos.append(
                    "ofrece un nivel de dificultad elevado"
                )

        if disponibilidad == "baja":
            if nombre in ["Running", "Yoga"]:
                puntaje += 2
                motivos.append(
                    "puede adaptarse a sesiones relativamente cortas"
                )

        elif disponibilidad == "media":
            if deporte["frecuencia"] in [
                "2 - 4 veces por semana",
                "3 - 4 veces por semana"
            ]:
                puntaje += 2
                motivos.append(
                    "su frecuencia puede adaptarse a una disponibilidad media"
                )

        elif disponibilidad == "alta":
            puntaje += 2
            motivos.append(
                "permite una frecuencia de práctica regular"
            )

        if presupuesto == "bajo":
            if nombre in ["Running", "Yoga"]:
                puntaje += 3
                motivos.append(
                    "puede practicarse con un costo relativamente bajo"
                )

        elif presupuesto == "medio":
            if nombre not in ["Tenis"]:
                puntaje += 2

        elif presupuesto == "alto":
            puntaje += 2
            motivos.append(
                "el presupuesto indicado permite considerar esta disciplina"
            )

        resultados.append({
            "nombre": nombre,
            "puntaje": puntaje,
            "motivos": motivos,
            "deporte": deporte
        })

    resultados.sort(
        key=lambda resultado: resultado["puntaje"],
        reverse=True
    )

    return resultados[:3]