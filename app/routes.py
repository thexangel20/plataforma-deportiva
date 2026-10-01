from __future__ import annotations

from flask import render_template, request

from app import app
from app.repositories import RepositoryError, get_repository


def _selected_ids() -> list[str]:
    """Lee ids repetidos o separados por coma y elimina duplicados."""

    raw_values = request.args.getlist("ids")
    selected: list[str] = []
    for raw_value in raw_values:
        for value in raw_value.split(","):
            sport_id = value.strip()
            if sport_id and sport_id not in selected:
                selected.append(sport_id)
    return selected


@app.route("/")
def inicio():
    error = None
    try:
        deportes = get_repository().list_all()
    except RepositoryError:
        deportes = []
        error = "No fue posible cargar el catálogo. Intenta nuevamente más tarde."
    return render_template("index.html", deportes=deportes, error=error)


@app.route("/comparar")
def comparar():
    selected_ids = _selected_ids()
    if len(selected_ids) < 2:
        return render_template(
            "comparar.html",
            deportes=[],
            error="Debes seleccionar al menos dos deportes.",
        ), 400

    try:
        deportes = get_repository().get_by_ids(selected_ids)
    except RepositoryError:
        return render_template(
            "comparar.html",
            deportes=[],
            error="No fue posible consultar los deportes seleccionados.",
        ), 503

    if len(deportes) < 2:
        return render_template(
            "comparar.html",
            deportes=[],
            error="Uno o más deportes seleccionados ya no están disponibles.",
        ), 404

    return render_template("comparar.html", deportes=deportes, error=None)
