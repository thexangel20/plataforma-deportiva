from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for

from app import app
from app.recommendations import available_objectives, recommend_deportes
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


@app.route("/recomendar", methods=["GET", "POST"])
def recomendar():
    error = None
    enviado = request.method == "POST"
    preferencias = {
        "costo": request.form.get("costo", "").strip().lower(),
        "objetivo": request.form.get("objetivo", "").strip(),
        "tiempo": request.form.get("tiempo", "").strip(),
    }
    recomendaciones = []

    try:
        deportes = get_repository().list_all()
        objetivos = available_objectives(deportes)
    except RepositoryError:
        deportes = []
        objetivos = []
        error = "No fue posible cargar las preferencias. Intenta nuevamente más tarde."

    if enviado and not error:
        tiempo = None
        if preferencias["tiempo"]:
            try:
                tiempo = int(preferencias["tiempo"])
            except ValueError:
                error = "Selecciona un tiempo disponible válido."
            if tiempo is not None and tiempo <= 0:
                error = "El tiempo disponible debe ser mayor que cero."

        if preferencias["costo"] and preferencias["costo"] not in {"bajo", "medio", "alto"}:
            error = "Selecciona un nivel de costo válido."

        if preferencias["objetivo"] and preferencias["objetivo"] not in objetivos:
            error = "Selecciona un objetivo disponible en la lista."

        if not error:
            recomendaciones = recommend_deportes(
                deportes,
                costo=preferencias["costo"],
                objetivo=preferencias["objetivo"],
                tiempo=tiempo,
            )

    return render_template(
        "recomendar.html",
        objetivos=objetivos,
        preferencias=preferencias,
        recomendaciones=recomendaciones,
        enviado=enviado,
        error=error,
    ), 400 if error and enviado else 200


@app.route("/admin/deportes")
def admin_deportes():
    """Panel administrativo de disponibilidad, conservando los registros."""

    error = None
    try:
        deportes = get_repository().list_all(include_inactive=True)
    except RepositoryError:
        deportes = []
        error = "No fue posible cargar la disponibilidad de los deportes."

    return render_template("admin_deportes.html", deportes=deportes, error=error)


@app.post("/admin/deportes/<sport_id>/estado")
def actualizar_estado_deporte(sport_id: str):
    """Activa o desactiva un deporte sin eliminarlo de la base de datos."""

    active_value = request.form.get("activo", "").strip().lower()
    if active_value not in {"true", "false"}:
        flash("El estado recibido no es válido.", "error")
        return redirect(url_for("admin_deportes")), 400

    try:
        deporte = get_repository().set_active(sport_id, active_value == "true")
    except RepositoryError:
        flash("No fue posible actualizar el estado del deporte.", "error")
        return redirect(url_for("admin_deportes")), 503

    if deporte is None:
        flash("El deporte solicitado no existe.", "error")
        return redirect(url_for("admin_deportes")), 404

    status_text = "activado" if deporte["activo"] else "desactivado"
    flash(f"{deporte['nombre']} fue {status_text} correctamente.", "success")
    return redirect(url_for("admin_deportes"))
