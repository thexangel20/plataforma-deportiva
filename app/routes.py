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
        "nivel": nivel, "objetivo": objetivo,
        "dias_disponibles": dias_disponibles, "horas_por_dia": horas_por_dia,
        "horas_recomendadas": horas_recomendadas, "carga_maxima": carga_maxima,
        "horas_reales": horas_reales, "duracion_sesion": duracion_sesion,
        "distribucion": distribucion, "advertencias": advertencias,
        "recomendaciones": recomendaciones,
    }


# ============================================================
# CALCULADORA DE DIETA Y NUTRICIÓN
# ============================================================

FACTORES_ACTIVIDAD = {
    "sedentario": 1.2, "ligero": 1.375, "moderado": 1.55,
    "intenso": 1.725, "muy_intenso": 1.9,
}

MACROS_POR_OBJETIVO = {
    "perder_grasa":   {"proteina": 0.40, "carbos": 0.30, "grasas": 0.30},
    "mantener":       {"proteina": 0.30, "carbos": 0.40, "grasas": 0.30},
    "ganar_musculo":  {"proteina": 0.30, "carbos": 0.50, "grasas": 0.20},
}

SUPLEMENTOS_POR_OBJETIVO = {
    "perder_grasa": {"costo": 400, "lista": ["Proteína whey (Bs 300)", "Multivitamínico (Bs 100)"]},
    "mantener": {"costo": 100, "lista": ["Multivitamínico (Bs 100)"]},
    "ganar_musculo": {"costo": 550, "lista": ["Proteína whey (Bs 300)", "Creatina (Bs 150)", "Multivitamínico (Bs 100)"]},
}


def calcular_dieta(sexo, edad, peso, altura, nivel_actividad, objetivo):
    """Calcula calorías, macros y presupuesto mensual en bolivianos."""

    if sexo == "masculino":
        tmb = (10 * peso) + (6.25 * altura) - (5 * edad) + 5
    else:
        tmb = (10 * peso) + (6.25 * altura) - (5 * edad) - 161

    factor = FACTORES_ACTIVIDAD[nivel_actividad]
    calorias_diarias = tmb * factor

    distribucion = MACROS_POR_OBJETIVO[objetivo]
    gramos_proteina = round((calorias_diarias * distribucion["proteina"]) / 4)
    gramos_carbos = round((calorias_diarias * distribucion["carbos"]) / 4)
    gramos_grasas = round((calorias_diarias * distribucion["grasas"]) / 9)

    diferencia_kcal = calorias_diarias - 2000
    if diferencia_kcal >= 0:
        ajuste = (diferencia_kcal / 100) * 0.50
    else:
        ajuste = (diferencia_kcal / 100) * 0.40
    presupuesto_super = round(1200 + ajuste)

    suplementos = SUPLEMENTOS_POR_OBJETIVO[objetivo]
    total_mensual = presupuesto_super + suplementos["costo"]

    recomendaciones = [
        f"Hidrátate: consume aproximadamente {round(peso * 0.035, 1)}L de agua al día.",
        f"Consume {gramos_proteina}g de proteína repartidos en 4-5 comidas.",
        "Prioriza carbohidratos complejos (avena, arroz integral, quinua).",
        "Incluye grasas saludables: palta, frutos secos, aceite de oliva.",
        "Come frutas y verduras de temporada (más económicas).",
    ]

    return {
        "sexo": sexo, "edad": edad, "peso": peso, "altura": altura,
        "nivel_actividad": nivel_actividad, "objetivo": objetivo,
        "tmb": round(tmb), "factor_actividad": factor,
        "calorias_diarias": round(calorias_diarias),
        "gramos_proteina": gramos_proteina, "gramos_carbos": gramos_carbos,
        "gramos_grasas": gramos_grasas, "presupuesto_super": presupuesto_super,
        "costo_suplementos": suplementos["costo"],
        "lista_suplementos": suplementos["lista"],
        "total_mensual": total_mensual, "recomendaciones": recomendaciones,
    }


# ============================================================
# OPTIMIZADOR DE COMPRAS USADOS VS NUEVOS
# ============================================================

IMPLEMENTOS_POR_DEPORTE = {
    "futbol":     ["Botines", "Balón", "Canilleras", "Guantes de arquero", "Uniforme"],
    "baloncesto": ["Zapatillas", "Balón", "Uniforme", "Rodilleras"],
    "natacion":   ["Traje de baño", "Gorro", "Gafas", "Aletas"],
    "tenis":      ["Raqueta", "Pelotas", "Zapatillas", "Overgrip"],
}

CONSEJOS_COMPRA_USADA = [
    "Inspecciona que no tenga grietas ni desgaste excesivo.",
    "Prueba la talla/ajuste antes de comprar.",
    "Verifica que el precio sea al menos 30% menor que el nuevo.",
    "Prefiere marcas reconocidas (más duraderas).",
    "Consulta política de devolución del vendedor.",
    "Revisa que no haya sido reparado sin garantía.",
]


def calcular_optimizacion(deporte, implemento, precio_nuevo, precio_usado, estado):
    if precio_usado >= precio_nuevo:
        return {
            "deporte": deporte, "implemento": implemento,
            "precio_nuevo": precio_nuevo, "precio_usado": precio_usado,
            "estado": estado, "ahorro": 0, "porcentaje": 0,
            "recomendacion": {
                "tipo": "warning", "titulo": "Datos inválidos",
                "mensaje": "El precio usado es mayor o igual al nuevo. Revisa los valores.",
            },
            "consejos": CONSEJOS_COMPRA_USADA,
        }

    ahorro = precio_nuevo - precio_usado
    porcentaje = round((ahorro / precio_nuevo) * 100, 1)

    estado_bueno = estado in ["como_nuevo", "bueno"]
    estado_regular = estado == "regular"

    if porcentaje >= 50 and estado_bueno:
        recomendacion = {"tipo": "success", "titulo": "Comprar usado ✅",
            "mensaje": f"El ahorro es significativo ({porcentaje}%) y el estado es óptimo."}
    elif porcentaje >= 50 and estado_regular:
        recomendacion = {"tipo": "warning", "titulo": "Comprar con precaución ⚠️",
            "mensaje": f"Ahorras {porcentaje}% pero el estado es regular."}
    elif 30 <= porcentaje < 50 and estado_bueno:
        recomendacion = {"tipo": "info", "titulo": "Considerar usado 💡",
            "mensaje": f"El ahorro es moderado ({porcentaje}%) y el estado es bueno."}
    elif 30 <= porcentaje < 50 and estado_regular:
        recomendacion = {"tipo": "warning", "titulo": "Pensar bien antes de comprar ⚠️",
            "mensaje": f"El ahorro ({porcentaje}%) no es tan alto y el estado es regular."}
    else:
        recomendacion = {"tipo": "error", "titulo": "Comprar nuevo ❌",
            "mensaje": f"El ahorro es bajo ({porcentaje}%). No vale la pena comprar usado."}

    return {
        "deporte": deporte, "implemento": implemento,
        "precio_nuevo": precio_nuevo, "precio_usado": precio_usado,
        "estado": estado, "ahorro": ahorro, "porcentaje": porcentaje,
        "recomendacion": recomendacion, "consejos": CONSEJOS_COMPRA_USADA,
    }


# ============================================================
# DESGASTE DE EQUIPAMIENTO POR DEPORTE
# ============================================================

# Catálogo con vida útil base (meses, uso estándar 3×/semana)
VIDA_UTIL_BASE = {
    "futbol": {
        "Botines": 12, "Balón": 6, "Canilleras": 24,
        "Guantes de arquero": 18, "Uniforme": 12,
    },
    "baloncesto": {
        "Zapatillas": 8, "Balón": 8, "Uniforme": 12, "Rodilleras": 12,
    },
    "natacion": {
        "Traje de baño": 6, "Gorro": 4, "Gafas": 12, "Aletas": 24,
    },
    "tenis": {
        "Raqueta": 24, "Pelotas": 2, "Zapatillas": 6, "Overgrip": 1,
    },
}


def calcular_desgaste(deporte, implemento, precio, vida_util_base, frecuencia):
    """Calcula vida útil ajustada y proyección de gastos."""

    # 1. Vida útil ajustada (base 3×/semana)
    vida_util_ajustada = round(vida_util_base * (3 / frecuencia), 1)

    # 2. Costo por mes
    costo_mensual = round(precio / vida_util_ajustada, 2)

    # 3. Proyecciones
    proyeccion_6m = round(costo_mensual * 6, 2)
    proyeccion_1a = round(costo_mensual * 12, 2)
    proyeccion_2a = round(costo_mensual * 24, 2)

    # 4. Número de compras
    compras_6m = round(6 / vida_util_ajustada, 2)
    compras_1a = round(12 / vida_util_ajustada, 2)
    compras_2a = round(24 / vida_util_ajustada, 2)

    # 5. Semáforo de desgaste según frecuencia
    if frecuencia <= 2:
        nivel_desgaste = {"nivel": "Bajo", "color": "verde", "emoji": "🟢"}
    elif frecuencia <= 4:
        nivel_desgaste = {"nivel": "Moderado", "color": "amarillo", "emoji": "🟡"}
    elif frecuencia <= 6:
        nivel_desgaste = {"nivel": "Alto", "color": "naranja", "emoji": "🟠"}
    else:
        nivel_desgaste = {"nivel": "Muy alto", "color": "rojo", "emoji": "🔴"}

    # 6. Barra de progreso visual (0-100%)
    # Vida útil restante como % (asumiendo uso actual)
    porcentaje_vida = 100

    # 7. Comparativa "Alternar 2 pares"
    vida_con_alternar = round(vida_util_ajustada * 2, 1)
    costo_mensual_alternar = round(precio / vida_con_alternar, 2)
    ahorro_anual_alternar = round((costo_mensual - costo_mensual_alternar) * 12, 2)

    # 8. Advertencias
    advertencias = []

    if vida_util_ajustada < 3:
        advertencias.append({
            "tipo": "warning",
            "mensaje": f"Con tu frecuencia, este implemento se reemplaza muy seguido "
                       f"({vida_util_ajustada} meses). Considera opciones más duraderas.",
        })

    if proyeccion_1a > 2000:
        advertencias.append({
            "tipo": "warning",
            "mensaje": f"El gasto anual estimado es considerable (Bs {proyeccion_1a}). "
                       f"Planifica tu presupuesto con antelación.",
        })

    if frecuencia >= 6:
        advertencias.append({
            "tipo": "info",
            "mensaje": "Con alta frecuencia, considera alternar 2 implementos para "
                       "duplicar su vida útil.",
        })

    if not advertencias:
        advertencias.append({
            "tipo": "success",
            "mensaje": "El desgaste está dentro de parámetros normales. ✅",
        })

    # 9. Recomendaciones personalizadas
    recomendaciones = [
        f"Reemplaza este implemento cada {vida_util_ajustada} meses aproximadamente.",
        f"Guarda Bs {costo_mensual} al mes para el próximo reemplazo.",
        "Revisa el estado del implemento cada 2 meses para anticipar el cambio.",
        "Límpialo y guárdalo correctamente para prolongar su vida útil.",
    ]

    if frecuencia >= 5:
        recomendaciones.append(
            "Con alta frecuencia, alternar 2 implementos puede duplicar su duración."
        )

    return {
        "deporte": deporte,
        "implemento": implemento,
        "precio": precio,
        "vida_util_base": vida_util_base,
        "frecuencia": frecuencia,
        "vida_util_ajustada": vida_util_ajustada,
        "costo_mensual": costo_mensual,
        "proyeccion_6m": proyeccion_6m,
        "proyeccion_1a": proyeccion_1a,
        "proyeccion_2a": proyeccion_2a,
        "compras_6m": compras_6m,
        "compras_1a": compras_1a,
        "compras_2a": compras_2a,
        "nivel_desgaste": nivel_desgaste,
        "porcentaje_vida": porcentaje_vida,
        "vida_con_alternar": vida_con_alternar,
        "costo_mensual_alternar": costo_mensual_alternar,
        "ahorro_anual_alternar": ahorro_anual_alternar,
        "advertencias": advertencias,
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
        resultado = calcular_plan(
            request.form.get("nivel", "principiante"),
            request.form.get("objetivo", "recreativo"),
            int(request.form.get("dias", 3)),
            float(request.form.get("horas", 1)),
        )
    return render_template("planificador.html", resultado=resultado)


@app.route("/dieta", methods=["GET", "POST"])
def dieta():
    resultado = None
    if request.method == "POST":
        resultado = calcular_dieta(
            request.form.get("sexo", "masculino"),
            int(request.form.get("edad", 20)),
            float(request.form.get("peso", 70)),
            float(request.form.get("altura", 170)),
            request.form.get("nivel_actividad", "moderado"),
            request.form.get("objetivo", "mantener"),
        )
    return render_template("dieta.html", resultado=resultado)


@app.route("/optimizador", methods=["GET", "POST"])
def optimizador():
    resultado = None
    if request.method == "POST":
        resultado = calcular_optimizacion(
            request.form.get("deporte", "futbol"),
            request.form.get("implemento", ""),
            float(request.form.get("precio_nuevo", 0)),
            float(request.form.get("precio_usado", 0)),
            request.form.get("estado", "bueno"),
        )
    return render_template(
        "optimizador.html",
        resultado=resultado,
        implementos_por_deporte=IMPLEMENTOS_POR_DEPORTE,
    )


@app.route("/desgaste", methods=["GET", "POST"])
def desgaste():
    resultado = None
    if request.method == "POST":
        deporte = request.form.get("deporte", "futbol")
        implemento = request.form.get("implemento", "")
        precio = float(request.form.get("precio", 0))
        vida_util_base = float(request.form.get("vida_util_base", 12))
        frecuencia = int(request.form.get("frecuencia", 3))

        resultado = calcular_desgaste(deporte, implemento, precio, vida_util_base, frecuencia)

    return render_template(
        "desgaste.html",
        resultado=resultado,
        vida_util_base=VIDA_UTIL_BASE,
    )