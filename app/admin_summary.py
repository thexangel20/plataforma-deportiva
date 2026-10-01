"""Cálculo del resumen administrativo de SportsInfo."""

from __future__ import annotations

from typing import Any, Iterable

from app.recommendations import cost_level


def build_admin_summary(deportes: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Construye métricas a partir del catálogo completo, activo e inactivo."""

    sports = list(deportes)
    distribution = {"bajo": 0, "medio": 0, "alto": 0}

    for deporte in sports:
        level = cost_level(deporte.get("costo"))
        if level in distribution:
            distribution[level] += 1

    total = len(sports)
    active = sum(1 for deporte in sports if deporte.get("activo", True))
    inactive = total - active

    return {
        "total": total,
        "activos": active,
        "inactivos": inactive,
        "por_costo": distribution,
    }
