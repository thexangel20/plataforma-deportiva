"""Acceso a los deportes para la aplicación.

El repositorio local permite ejecutar y revisar la HU21 sin credenciales de
Supabase. Cuando se configuran SUPABASE_URL y SUPABASE_KEY se utiliza la tabla
deportes de PostgreSQL mediante el cliente oficial de Supabase.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any, Iterable


class RepositoryError(RuntimeError):
    """Error controlado al consultar la fuente de datos."""


LOCAL_DEPORTE_DATA = [
    {
        "id": "futbol",
        "nombre": "Fútbol",
        "icono": "⚽",
        "descripcion": "Deporte colectivo de alta intensidad y coordinación.",
        "objetivo": "Resistencia y trabajo en equipo",
        "costo": 150,
        "moneda": "Bs.",
        "duracion_minutos": 90,
        "equipamiento": ["Balón", "Zapatillas deportivas", "Camiseta"],
        "recomendaciones": [
            "Realizar calentamiento antes de entrenar.",
            "Mantener una buena hidratación.",
        ],
        "imagen_url": None,
        "activo": True,
    },
    {
        "id": "baloncesto",
        "nombre": "Baloncesto",
        "icono": "🏀",
        "descripcion": "Disciplina dinámica que combina velocidad, precisión y estrategia.",
        "objetivo": "Agilidad y coordinación",
        "costo": 120,
        "moneda": "Bs.",
        "duracion_minutos": 90,
        "equipamiento": ["Balón de baloncesto", "Zapatillas deportivas", "Ropa cómoda"],
        "recomendaciones": [
            "Practicar lanzamientos y desplazamientos.",
            "Usar calzado con buen soporte.",
        ],
        "imagen_url": None,
        "activo": True,
    },
    {
        "id": "natacion",
        "nombre": "Natación",
        "icono": "🏊",
        "descripcion": "Actividad de bajo impacto que ejercita todo el cuerpo.",
        "objetivo": "Resistencia y bienestar físico",
        "costo": 200,
        "moneda": "Bs.",
        "duracion_minutos": 60,
        "equipamiento": ["Traje de baño", "Gafas de natación", "Gorro de natación"],
        "recomendaciones": [
            "Comenzar con una intensidad progresiva.",
            "Respetar las normas de seguridad de la piscina.",
        ],
        "imagen_url": None,
        "activo": True,
    },
    {
        "id": "tenis",
        "nombre": "Tenis",
        "icono": "🎾",
        "descripcion": "Deporte individual que desarrolla precisión, velocidad y estrategia.",
        "objetivo": "Coordinación y concentración",
        "costo": 300,
        "moneda": "Bs.",
        "duracion_minutos": 120,
        "equipamiento": ["Raqueta", "Pelotas de tenis", "Zapatillas de cancha"],
        "recomendaciones": [
            "Practicar la técnica con supervisión.",
            "Realizar pausas de recuperación durante la sesión.",
        ],
        "imagen_url": None,
        "activo": True,
    },
]


def _as_list(value: Any) -> list[str]:
    """Normaliza arrays de PostgreSQL/Supabase a listas de texto."""

    if value is None:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return [value]
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def normalize_deporte(row: dict[str, Any]) -> dict[str, Any]:
    """Adapta una fila de Supabase al contrato usado por las plantillas."""

    normalized = dict(row)
    normalized["id"] = str(normalized.get("id", "")).strip()
    normalized["nombre"] = str(normalized.get("nombre", "")).strip()
    normalized["icono"] = normalized.get("icono") or "🏅"
    normalized["descripcion"] = normalized.get("descripcion") or ""
    normalized["objetivo"] = normalized.get("objetivo") or "No especificado"
    normalized["moneda"] = normalized.get("moneda") or "Bs."
    normalized["costo"] = normalized.get("costo", 0)
    normalized["duracion_minutos"] = normalized.get("duracion_minutos", 0)
    normalized["equipamiento"] = _as_list(normalized.get("equipamiento"))
    normalized["recomendaciones"] = _as_list(normalized.get("recomendaciones"))
    normalized["imagen_url"] = normalized.get("imagen_url")
    active_value = normalized.get("activo", True)
    if isinstance(active_value, str):
        normalized["activo"] = active_value.strip().lower() not in {"false", "0", "no", ""}
    else:
        normalized["activo"] = bool(active_value)
    return normalized


class LocalRepository:
    """Repositorio de demostración para desarrollo sin Supabase."""

    def list_all(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        sports = LOCAL_DEPORTE_DATA
        if not include_inactive:
            sports = [sport for sport in sports if sport.get("activo", True)]
        return deepcopy(sports)

    def get_by_ids(self, ids: Iterable[str]) -> list[dict[str, Any]]:
        requested = [str(value) for value in ids]
        by_id = {sport["id"]: sport for sport in LOCAL_DEPORTE_DATA}
        return [
            deepcopy(by_id[sport_id])
            for sport_id in requested
            if sport_id in by_id and by_id[sport_id].get("activo", True)
        ]

    def set_active(self, sport_id: str, active: bool) -> dict[str, Any] | None:
        for sport in LOCAL_DEPORTE_DATA:
            if sport["id"] == sport_id:
                sport["activo"] = active
                return deepcopy(sport)
        return None


class SupabaseRepository:
    """Repositorio contra la tabla deportes de Supabase/PostgreSQL."""

    def __init__(self, url: str, key: str) -> None:
        try:
            from supabase import create_client
        except ImportError as exc:
            raise RepositoryError(
                "Falta instalar la dependencia supabase. Ejecuta pip install -r requirements-supabase.txt."
            ) from exc

        self.client = create_client(url, key)

    def list_all(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        query = self.client.table("deportes").select("*")
        if not include_inactive:
            query = query.eq("activo", True)
        response = query.order("nombre").execute()
        return [normalize_deporte(row) for row in (response.data or [])]

    def get_by_ids(self, ids: Iterable[str]) -> list[dict[str, Any]]:
        requested = [str(value) for value in ids]
        if not requested:
            return []

        response = (
            self.client.table("deportes")
            .select("*")
            .in_("id", requested)
            .eq("activo", True)
            .execute()
        )
        by_id = {str(row.get("id")): normalize_deporte(row) for row in (response.data or [])}
        return [by_id[sport_id] for sport_id in requested if sport_id in by_id]

    def set_active(self, sport_id: str, active: bool) -> dict[str, Any] | None:
        response = (
            self.client.table("deportes")
            .update({"activo": active})
            .eq("id", sport_id)
            .select("*")
            .execute()
        )
        if not response.data:
            return None
        return normalize_deporte(response.data[0])


def get_repository() -> LocalRepository | SupabaseRepository:
    """Devuelve Supabase si está configurado; local en caso contrario."""

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() or os.getenv("SUPABASE_KEY", "").strip()
    if url and key:
        return SupabaseRepository(url, key)
    return LocalRepository()
