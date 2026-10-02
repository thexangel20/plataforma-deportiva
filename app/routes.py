from flask import render_template, request
from app import app


# ============================================================
# PLANIFICADOR DE ENTRENAMIENTO
# ============================================================

HORAS_RECOMENDADAS = {
    "principiante": {"recreativo": 3, "salud": 4, "competitivo": 5},
    "intermedio":   {"recreativo": 5, "salud": 6, "competitivo": 8},
    "avanzado":     {"recreativo": 7, "salud": 8, "competitivo": 12},
}

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def calcular_plan(nivel, objetivo, dias_disponibles, horas_por_dia):
    """Calcula el plan de entrenamiento según los datos del usuario."""

    horas_recomendadas = HORAS_RECOMENDADAS[nivel][objetivo]
    carga_maxima = dias_disponibles * horas_por_dia
    horas_reales = min(horas_recomendadas, carga_maxima)
    duracion_sesion = round(horas_reales / dias_disponibles, 2)

    distribucion = []
    paso = 7 / dias_disponibles
    indices_sesion = []
    for i in range(dias_disponibles):
        indice = int(round(i * paso)) % 7
        if indice not in indices_sesion:
            indices_sesion.append(indice)

    j = 0
    while len(indices_sesion) < dias_disponibles and j < 7:
        if j not in indices_sesion:
            indices_sesion.append(j)
        j += 1

    indices_sesion = sorted(indices_sesion)

    for i, dia in enumerate(DIAS_SEMANA):
        if i in indices_sesion:
            distribucion.append({"dia": dia, "entrena": True, "duracion": duracion_sesion})
        else:
            distribucion.append({"dia": dia, "entrena": False, "duracion": 0})

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


# ============================================================
# CALCULADORA DE DIETA Y NUTRICIÓN
# ============================================================

FACTORES_ACTIVIDAD = {
    "sedentario": 1.2,
    "ligero": 1.375,
    "moderado": 1.55,
    "intenso": 1.725,
    "muy_intenso": 1.9,
}

MACROS_POR_OBJETIVO = {
    "perder_grasa":   {"proteina": 0.40, "carbos": 0.30, "grasas": 0.30},
    "mantener":       {"proteina": 0.30, "carbos": 0.40, "grasas": 0.30},
    "ganar_musculo":  {"proteina": 0.30, "carbos": 0.50, "grasas": 0.20},
}

SUPLEMENTOS_POR_OBJETIVO = {
    "perder_grasa": {
        "costo": 400,
        "lista": ["Proteína whey (Bs 300)", "Multivitamínico (Bs 100)"],
    },
    "mantener": {
        "costo": 100,
        "lista": ["Multivitamínico (Bs 100)"],
    },
    "ganar_musculo": {
        "costo": 550,
        "lista": [
            "Proteína whey (Bs 300)",
            "Creatina (Bs 150)",
            "Multivitamínico (Bs 100)",
        ],
    },
}


def calcular_dieta(sexo, edad, peso, altura, nivel_actividad, objetivo):
    """Calcula calorías, macros y presupuesto mensual en bolivianos."""

    # 1. TMB — Fórmula Mifflin-St Jeor
    if sexo == "masculino":
        tmb = (10 * peso) + (6.25 * altura) - (5 * edad) + 5
    else:
        tmb = (10 * peso) + (6.25 * altura) - (5 * edad) - 161

    # 2. Calorías diarias totales
    factor = FACTORES_ACTIVIDAD[nivel_actividad]
    calorias_diarias = tmb * factor

    # 3. Macronutrientes
    distribucion = MACROS_POR_OBJETIVO[objetivo]
    gramos_proteina = round((calorias_diarias * distribucion["proteina"]) / 4)
    gramos_carbos = round((calorias_diarias * distribucion["carbos"]) / 4)
    gramos_grasas = round((calorias_diarias * distribucion["grasas"]) / 9)

    # 4. Presupuesto de supermercado (Bs)
    # Base: Bs 1,200 para 2,000 kcal/día
    # Ajuste: +Bs 0.50 por cada 100 kcal extra, -Bs 0.40 por cada 100 kcal menos
    diferencia_kcal = calorias_diarias - 2000
    if diferencia_kcal >= 0:
        ajuste = (diferencia_kcal / 100) * 0.50
    else:
        ajuste = (diferencia_kcal / 100) * 0.40
    presupuesto_super = round(1200 + ajuste)

    # 5. Suplementos
    suplementos = SUPLEMENTOS_POR_OBJETIVO[objetivo]

    # 6. Total
    total_mensual = presupuesto_super + suplementos["costo"]

    # 7. Recomendaciones
    recomendaciones = [
        f"Hidrátate: consume aproximadamente {round(peso * 0.035, 1)}L de agua al día.",
        f"Consume {gramos_proteina}g de proteína repartidos en 4-5 comidas.",
        "Prioriza carbohidratos complejos (avena, arroz integral, quinua).",
        "Incluye grasas saludables: palta, frutos secos, aceite de oliva.",
        "Come frutas y verduras de temporada (más económicas).",
    ]

    return {
        "sexo": sexo,
        "edad": edad,
        "peso": peso,
        "altura": altura,
        "nivel_actividad": nivel_actividad,
        "objetivo": objetivo,
        "tmb": round(tmb),
        "factor_actividad": factor,
        "calorias_diarias": round(calorias_diarias),
        "gramos_proteina": gramos_proteina,
        "gramos_carbos": gramos_carbos,
        "gramos_grasas": gramos_grasas,
        "presupuesto_super": presupuesto_super,
        "costo_suplementos": suplementos["costo"],
        "lista_suplementos": suplementos["lista"],
        "total_mensual": total_mensual,
        "recomendaciones": recomendaciones,
    }


# ============================================================
# RUTAS
# ============================================================

@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/planificador", methods=["GET", "POST"])
def planificador():
    resultado = None

    if request.method == "POST":
        nivel = request.form.get("nivel", "principiante")
        objetivo = request.form.get("objetivo", "recreativo")
        dias = int(request.form.get("dias", 3))
        horas = float(request.form.get("horas", 1))
        resultado = calcular_plan(nivel, objetivo, dias, horas)

    return render_template("planificador.html", resultado=resultado)


@app.route("/dieta", methods=["GET", "POST"])
def dieta():
    resultado = None

    if request.method == "POST":
        sexo = request.form.get("sexo", "masculino")
        edad = int(request.form.get("edad", 20))
        peso = float(request.form.get("peso", 70))
        altura = float(request.form.get("altura", 170))
        nivel_actividad = request.form.get("nivel_actividad", "moderado")
        objetivo = request.form.get("objetivo", "mantener")

        resultado = calcular_dieta(sexo, edad, peso, altura, nivel_actividad, objetivo)

    return render_template("dieta.html", resultado=resultado)