"""Reglas de recomendación para la HU22."""

from __future__ import annotations

from typing import Any, Iterable


COST_LEVELS = {
    "bajo": (0, 150),
    "medio": (151, 250),
    "alto": (251, float("inf")),
}


def cost_level(cost: Any) -> str:
    """Convierte el costo numérico a la categoría usada por el formulario."""

    try:
        amount = float(cost)
    except (TypeError, ValueError):
        return ""

    for level, (minimum, maximum) in COST_LEVELS.items():
        if minimum <= amount <= maximum:
            return level
    return ""


def available_objectives(deportes: Iterable[dict[str, Any]]) -> list[str]:
    """Obtiene objetivos únicos para llenar el selector dinámicamente."""

    objectives = {
        str(deporte.get("objetivo", "")).strip()
        for deporte in deportes
        if str(deporte.get("objetivo", "")).strip()
    }
    return sorted(objectives, key=str.casefold)


def recommend_deportes(
    deportes: Iterable[dict[str, Any]],
    *,
    costo: str = "",
    objetivo: str = "",
    tiempo: int | None = None,
) -> list[dict[str, Any]]:
    """Devuelve deportes que cumplen todas las preferencias indicadas.

    El resultado incluye ``coincidencias`` para que la interfaz pueda explicar
    por qué cada deporte fue recomendado. Los criterios vacíos no restringen.
    """

    normalized_cost = costo.strip().lower()
    normalized_objective = objetivo.strip().casefold()
    recommendations: list[dict[str, Any]] = []

    for deporte in deportes:
        matches = 0
        criteria = 0

        if normalized_cost:
            criteria += 1
            if cost_level(deporte.get("costo")) == normalized_cost:
                matches += 1
            else:
                continue

        if normalized_objective:
            criteria += 1
            if str(deporte.get("objetivo", "")).strip().casefold() == normalized_objective:
                matches += 1
            else:
                continue

        if tiempo is not None:
            criteria += 1
            try:
                duration = int(deporte.get("duracion_minutos", 0))
            except (TypeError, ValueError):
                duration = 0
            if duration <= tiempo:
                matches += 1
            else:
                continue

        recommendation = dict(deporte)
        recommendation["nivel_costo"] = cost_level(deporte.get("costo"))
        recommendation["coincidencias"] = matches
        recommendation["criterios"] = criteria
        recommendations.append(recommendation)

    return sorted(
        recommendations,
        key=lambda deporte: (-(deporte["coincidencias"]), deporte["nombre"].casefold()),
    )
