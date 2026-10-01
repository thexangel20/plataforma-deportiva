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
    return normalized


class LocalRepository:
    """Repositorio de demostración para desarrollo sin Supabase."""

    def list_all(self) -> list[dict[str, Any]]:
        return deepcopy(LOCAL_DEPORTE_DATA)

    def get_by_ids(self, ids: Iterable[str]) -> list[dict[str, Any]]:
        requested = [str(value) for value in ids]
        by_id = {sport["id"]: sport for sport in LOCAL_DEPORTE_DATA}
        return [deepcopy(by_id[sport_id]) for sport_id in requested if sport_id in by_id]


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

    def list_all(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("deportes")
            .select("*")
            .eq("activo", True)
            .order("nombre")
            .execute()
        )
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


def get_repository() -> LocalRepository | SupabaseRepository:
    """Devuelve Supabase si está configurado; local en caso contrario."""

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()
    if url and key:
        return SupabaseRepository(url, key)
    return LocalRepository()
