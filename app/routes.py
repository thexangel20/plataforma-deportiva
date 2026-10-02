from flask import render_template, request
from app import app


# Matriz de horas semanales recomendadas por nivel + objetivo
HORAS_RECOMENDADAS = {
    "principiante": {"recreativo": 3, "salud": 4, "competitivo": 5},
    "intermedio":   {"recreativo": 5, "salud": 6, "competitivo": 8},
    "avanzado":     {"recreativo": 7, "salud": 8, "competitivo": 12},
}

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def calcular_plan(nivel, objetivo, dias_disponibles, horas_por_dia):
    """Calcula el plan de entrenamiento según los datos del usuario."""

    # 1. Horas recomendadas según nivel + objetivo
    horas_recomendadas = HORAS_RECOMENDADAS[nivel][objetivo]

    # 2. Carga máxima permitida por el usuario
    carga_maxima = dias_disponibles * horas_por_dia

    # 3. Horas reales a usar (no más de lo recomendado ni de lo disponible)
    horas_reales = min(horas_recomendadas, carga_maxima)

    # 4. Duración por sesión
    duracion_sesion = round(horas_reales / dias_disponibles, 2)

    # 5. Distribución semanal (intercalando descansos)
    # Se reparten las sesiones en los días disponibles, dejando días de descanso entre medio
    distribucion = []
    paso = 7 / dias_disponibles  # Para intercalar los días
    indices_sesion = []
    for i in range(dias_disponibles):
        indice = int(round(i * paso)) % 7
        if indice not in indices_sesion:
            indices_sesion.append(indice)

    # Si no se lograron todos los índices, rellenar
    j = 0
    while len(indices_sesion) < dias_disponibles and j < 7:
        if j not in indices_sesion:
            indices_sesion.append(j)
        j += 1

    indices_sesion = sorted(indices_sesion)

    for i, dia in enumerate(DIAS_SEMANA):
        if i in indices_sesion:
            distribucion.append({
                "dia": dia,
                "entrena": True,
                "duracion": duracion_sesion,
            })
        else:
            distribucion.append({
                "dia": dia,
                "entrena": False,
                "duracion": 0,
            })

    # 6. Advertencias
    advertencias = []

    if carga_maxima < horas_recomendadas:
        advertencias.append({
            "tipo": "warning",
            "mensaje": f"Con tu disponibilidad ({carga_maxima}h/semana) no alcanzas las "
                       f"{horas_recomendadas}h recomendadas para tu nivel y objetivo."
        })

    if carga_maxima > horas_recomendadas * 1.5:
        advertencias.append({
            "tipo": "warning",
            "mensaje": f"Tu disponibilidad ({carga_maxima}h/semana) supera ampliamente lo "
                       f"recomendado ({horas_recomendadas}h). Podrías sobreentrenar."
        })

    if nivel == "principiante" and objetivo == "competitivo":
        advertencias.append({
            "tipo": "info",
            "mensaje": "Como principiante con objetivo competitivo, aumenta la carga "
                       "progresivamente durante las primeras semanas."
        })

    if not advertencias:
        advertencias.append({
            "tipo": "success",
            "mensaje": "Tu plan está bien ajustado a tu nivel y disponibilidad. ✅"
        })

    # 7. Recomendaciones generales
    recomendaciones = [
        "Calienta 5-10 minutos antes de cada sesión.",
        "Bebe agua antes, durante y después del entrenamiento.",
        "Incluye al menos un día completo de descanso a la semana.",
        "Duerme entre 7 y 8 horas para una buena recuperación.",
    ]

    return {
        "nivel": nivel,
        "objetivo": objetivo,
        "dias_disponibles": dias_disponibles,
        "horas_por_dia": horas_por_dia,
        "horas_recomendadas": horas_recomendadas,
        "carga_maxima": carga_maxima,
        "horas_reales": horas_reales,
        "duracion_sesion": duracion_sesion,
        "distribucion": distribucion,
        "advertencias": advertencias,
        "recomendaciones": recomendaciones,
    }


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/planificador", methods=["GET", "POST"])
def planificador():
    resultado = None

    if request.method == "POST":
        # Obtener datos del formulario
        nivel = request.form.get("nivel", "principiante")
        objetivo = request.form.get("objetivo", "recreativo")
        dias = int(request.form.get("dias", 3))
        horas = float(request.form.get("horas", 1))

        # Calcular el plan
        resultado = calcular_plan(nivel, objetivo, dias, horas)

    return render_template("planificador.html", resultado=resultado)