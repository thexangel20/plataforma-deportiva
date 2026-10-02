import re
import secrets
import time
import unicodedata
import warnings
from datetime import datetime, timezone
from functools import wraps
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, abort, current_app, flash, g, jsonify, redirect, render_template, request, send_file, send_from_directory, session, url_for
from itsdangerous import BadSignature, URLSafeTimedSerializer
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.security import check_password_hash, generate_password_hash

from .calculations import GOALS, LEVELS, CATEGORIES, number, money, choice, budget, wear, shopping, plan, recommendations
from .store import Conflict, DataError


bp = Blueprint('web', __name__)


def db():
    return current_app.extensions['store']


def now():
    return datetime.now(timezone.utc).isoformat()


def csrf():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_hex(32)
    return session['csrf']


@bp.before_app_request
def identify():
    g.user = None
    if session.get('user_id'):
        g.user = db().get('usuarios', session['user_id'])
        if not g.user:
            session.clear()
    if request.method == 'POST':
        token = request.form.get('csrf', '')
        if not token or not secrets.compare_digest(token.encode(), session.get('csrf', '').encode()):
            abort(400)


@bp.app_context_processor
def context():
    return {'csrf': csrf, 'goals': GOALS, 'levels': LEVELS,
            'local_mode': current_app.config['DATA_BACKEND'] == 'local',
            'sport_cost': sport_cost, 'sport_image': sport_image}


def authenticated(admin=False):
    def decorate(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user:
                flash('Inicia sesión para continuar.', 'info')
                return redirect(url_for('web.login'))
            if admin and g.user['rol'] != 'admin':
                abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorate


def sport_cost(sport):
    if sport['costo'] is None:
        return 'Por confirmar'
    return f"{sport['costo']:,.2f} {sport['moneda']} / {sport['periodo']}"


def sport_image(sport):
    image = sport.get('imagen') or ''
    if image.startswith(('https://', 'http://', '/')):
        return image
    identifier = re.sub(r'[^a-z0-9_-]', '', sport.get('id', '').lower())
    if identifier:
        return url_for('static', filename='photos/' + identifier + '.jpg')
    return url_for('static', filename='brand.svg')


def sport_by_id(identifier, inactive=False):
    sport = db().get('deportes', identifier)
    if not sport or (not sport['activo'] and not inactive):
        abort(404)
    return sport


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn')


def catalog():
    query = request.args.get('q', '').strip()[:100]
    level = request.args.get('costo', '')
    if level not in ('', 'bajo', 'medio', 'alto'):
        abort(400)
    result = sorted(db().all('deportes', activo=True), key=lambda s: s['nombre'])
    if query:
        result = [s for s in result if normalized(query) in normalized(s['nombre'] + ' ' + s['objetivo'] + ' ' + ' '.join(GOALS.get(k, k) for k in s['objetivo'].split(',')))]
    if level:
        result = [s for s in result if s['costo'] is not None and s['moneda'] == 'BOB' and s['periodo'] == 'mes' and
                  ('bajo' if s['costo'] <= 150 else 'medio' if s['costo'] <= 300 else 'alto') == level]
    return result, query, level


@bp.route('/')
def home():
    sports, query, level = catalog()
    favorite_ids = {f['deporte_id'] for f in db().all('favoritos', usuario_id=g.user['id'])} if g.user else set()
    return render_template('index.html', sports=sports, query=query, cost_level=level, favorite_ids=favorite_ids)


@bp.route('/catalogo/resultados')
def results():
    sports, _, _ = catalog()
    favorite_ids = {f['deporte_id'] for f in db().all('favoritos', usuario_id=g.user['id'])} if g.user else set()
    return jsonify(html=render_template('_cards.html', sports=sports, favorite_ids=favorite_ids), count=len(sports))


@bp.route('/deportes/<identifier>')
def detail(identifier):
    sport = sport_by_id(identifier, bool(g.user and g.user['rol'] == 'admin'))
    favorite = bool(g.user and db().all('favoritos', usuario_id=g.user['id'], deporte_id=identifier))
    return render_template('detail.html', sport=sport, favorite=favorite)


@bp.route('/registro', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = text(request.form, 'nombre', 2, 80)
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            if len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
                raise ValueError('Ingresa un correo válido.')
            if not 10 <= len(password) <= 128:
                raise ValueError('La contraseña debe tener entre 10 y 128 caracteres.')
            if password != request.form.get('confirmacion'):
                raise ValueError('Las contraseñas no coinciden.')
            db().add('usuarios', dict(id=uuid4().hex, email=email, nombre=name,
                     password_hash=generate_password_hash(password), rol='usuario', creado=now()))
            flash('Cuenta creada. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('web.login'))
        except (ValueError, Conflict) as error:
            flash('Ese correo ya tiene una cuenta.' if isinstance(error, Conflict) else str(error), 'error')
            return render_template('auth.html', registering=True), 400
    return render_template('auth.html', registering=True)


@bp.route('/ingresar', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()[:254]
        attempts = current_app.extensions['login_attempts']
        clock = time.monotonic()
        for key in list(attempts):
            if attempts[key][1] < clock - 900:
                attempts.pop(key)
        key = (request.remote_addr, email)
        count, last = attempts.get(key, (0, clock))
        if count >= 10:
            flash('Demasiados intentos. Vuelve a intentarlo en 15 minutos.', 'error')
            return render_template('auth.html', registering=False), 429
        users = db().all('usuarios', email=email)
        password = request.form.get('password', '')
        if users and len(password) <= 128 and check_password_hash(users[0]['password_hash'], password):
            session.clear()
            session['user_id'] = users[0]['id']
            session.permanent = True
            attempts.pop(key, None)
            return redirect(url_for('web.home'))
        attempts[key] = (count + 1, last)
        flash('Correo o contraseña incorrectos.', 'error')
        return render_template('auth.html', registering=False), 400
    return render_template('auth.html', registering=False)


@bp.post('/salir')
def logout():
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('web.home'))


@bp.route('/favoritos')
@authenticated()
def favorites():
    rows = db().all('favoritos', usuario_id=g.user['id'])
    sports = [db().get('deportes', row['deporte_id']) for row in rows]
    return render_template('favorites.html', sports=[s for s in sports if s], favorite_ids={r['deporte_id'] for r in rows})


@bp.post('/favoritos/<identifier>/<action>')
@authenticated()
def favorite_action(identifier, action):
    if action not in ('agregar', 'quitar'):
        abort(404)
    sport_by_id(identifier, action == 'quitar')
    rows = db().all('favoritos', usuario_id=g.user['id'], deporte_id=identifier)
    if action == 'agregar' and not rows:
        try:
            db().add('favoritos', dict(id=uuid4().hex, usuario_id=g.user['id'], deporte_id=identifier))
        except Conflict:
            pass
    elif action == 'quitar':
        for row in rows:
            db().delete('favoritos', row['id'])
    flash('Tu lista de favoritos está actualizada.', 'success')
    return redirect(url_for('web.favorites'))


@bp.route('/perfil', methods=['GET', 'POST'])
@authenticated()
def profile():
    previous = db().get('perfiles', g.user['id'])
    if request.method == 'POST':
        try:
            form = request.form
            row = dict(id=g.user['id'], edad=number(form.get('edad'), 'Edad', 13, 100, True),
                       peso=float(number(form['peso'], 'Peso', 20, 350)) if form.get('peso') else None,
                       altura=float(number(form['altura'], 'Altura', 80, 250)) if form.get('altura') else None,
                       sexo=choice(form.get('sexo'), ['no_indicar', 'femenino', 'masculino', 'otro'], 'sexo'),
                       experiencia=choice(form.get('experiencia'), LEVELS, 'experiencia'),
                       objetivo=choice(form.get('objetivo'), GOALS, 'objetivo'),
                       presupuesto=float(money(number(form.get('presupuesto'), 'Presupuesto'))),
                       dias=number(form.get('dias'), 'Días', 1, 7, True),
                       minutos=number(form.get('minutos'), 'Minutos', 15, 240, True))
            db().update('perfiles', g.user['id'], row) if previous else db().add('perfiles', row)
            flash('Perfil guardado. Tus recomendaciones ya están actualizadas.', 'success')
            return redirect(url_for('web.recommend'))
        except ValueError as error:
            flash(str(error), 'error')
            return render_template('profile.html', profile=request.form), 400
    return render_template('profile.html', profile=previous or {})


@bp.route('/recomendaciones')
@authenticated()
def recommend():
    profile = db().get('perfiles', g.user['id'])
    if not profile:
        flash('Completa tu perfil para obtener recomendaciones.', 'info')
        return redirect(url_for('web.profile'))
    return render_template('recommend.html', results=recommendations(db().all('deportes', activo=True), profile), profile=profile)


FIELDS = [('costo', 'Costo orientativo'), ('minutos', 'Duración por sesión'), ('equipamiento', 'Equipamiento'),
          ('dificultad', 'Dificultad de entrada'), ('beneficios', 'Beneficios'), ('condiciones', 'Condiciones del lugar')]


def signer():
    return URLSafeTimedSerializer(current_app.secret_key, salt='sportsinfo-comparison-v1')


@bp.route('/comparar')
def compare():
    ids = request.args.getlist('deporte')
    preselection = request.args.get('preseleccion')
    sports = db().all('deportes', activo=True)
    selected = []
    status = 200
    if ids:
        if len(ids) not in (2, 3) or len(set(ids)) != len(ids):
            flash('Selecciona dos o tres deportes distintos.', 'error')
            status = 400
        else:
            selected = [sport_by_id(i) for i in ids]
    if preselection and not ids:
        sport_by_id(preselection)
        ids = [preselection]
    snapshot = {'sports': selected, 'created': now()}
    return render_template('compare.html', sports=sports, selected=selected,
                           selected_ids=ids, fields=FIELDS, snapshot_token=signer().dumps(snapshot) if selected else ''), status


@bp.post('/comparar/pdf')
def compare_pdf():
    try:
        snapshot = signer().loads(request.form.get('snapshot', ''), max_age=3600)
        if not isinstance(snapshot, dict) or len(snapshot.get('sports', [])) not in (2, 3):
            abort(400)
    except BadSignature:
        flash('La comparación venció. Vuelve a generarla para descargar el PDF.', 'error')
        return redirect(url_for('web.compare'))
    from .pdf import render_pdf
    content = render_pdf(snapshot, FIELDS, sport_cost)
    return send_file(BytesIO(content), mimetype='application/pdf', as_attachment=True, download_name='SportsInfo-comparacion.pdf')


@bp.route('/herramientas')
def tools_page():
    return render_template('tools.html')


@bp.route('/herramientas/<kind>', methods=['GET', 'POST'])
def calculator(kind):
    titles = {'presupuesto': 'Tu presupuesto deportivo', 'desgaste': 'Vida útil de tu equipamiento',
              'plan': 'Organiza tu semana', 'compras': 'Una compra con más información'}
    if kind not in titles:
        abort(404)
    result, status = None, 200
    sports = db().all('deportes', activo=True)
    if request.method == 'POST':
        try:
            if kind == 'presupuesto':
                sport = sport_by_id(request.form.get('deporte', ''))
                result = budget(request.form)
                result['sport'] = sport['nombre']
            elif kind == 'desgaste':
                result = wear(request.form)
                result['item'] = text(request.form, 'implemento', 2, 100)
            elif kind == 'compras':
                result = shopping(request.form)
                result['item'] = text(request.form, 'implemento', 2, 100)
            else:
                result = plan(request.form, sport_by_id(request.form.get('deporte', '')))
        except ValueError as error:
            flash(str(error), 'error')
            status = 400
            result = None
    return render_template('calculator.html', kind=kind, title=titles[kind], result=result,
                           sports=sports, categories=CATEGORIES), status


def text(form, key, minimum=1, maximum=3000):
    value = form.get(key, '').strip()
    if not minimum <= len(value) <= maximum:
        raise ValueError(f'{key.replace("_", " ").capitalize()}: escribe entre {minimum} y {maximum} caracteres.')
    return value


@bp.route('/deportes/<identifier>/reportar', methods=['GET', 'POST'])
def report(identifier):
    sport = sport_by_id(identifier)
    if request.method == 'POST':
        try:
            field = choice(request.form.get('campo'), ['costos', 'equipamiento', 'alimentacion', 'condiciones', 'otro'], 'campo')
            description = text(request.form, 'descripcion', 10, 1000)
            db().add('reportes', dict(id=uuid4().hex, deporte_id=identifier,
                     usuario_id=g.user['id'] if g.user else None, campo=field,
                     descripcion=description, estado='pendiente', creado=now()))
            flash('Reporte recibido. El equipo revisará la información.', 'success')
            return redirect(url_for('web.detail', identifier=identifier))
        except ValueError as error:
            flash(str(error), 'error')
            return render_template('report.html', sport=sport), 400
    return render_template('report.html', sport=sport)


@bp.route('/admin')
@authenticated(admin=True)
def admin():
    sports = db().all('deportes')
    reports = db().all('reportes')
    names = {s['id']: s['nombre'] for s in sports}
    return render_template('admin.html', sports=sports, reports=sorted(reports, key=lambda r: r['creado'], reverse=True), names=names)


def upload_image(file):
    payload = file.read(5 * 1024 * 1024 + 1)
    if len(payload) > 5 * 1024 * 1024:
        raise ValueError('La imagen debe pesar como máximo 5 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(payload)) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 16000000:
                    raise ValueError('Usa una imagen JPEG, PNG o WebP de hasta 16 millones de píxeles.')
                image = ImageOps.exif_transpose(image).convert('RGB')
                image.thumbnail((1600, 1200))
                output = BytesIO()
                image.save(output, 'JPEG', quality=85)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('El archivo no es una imagen válida.') from None
    filename = uuid4().hex + '.jpg'
    if db().remote:
        return db().upload(current_app.config['SUPABASE_BUCKET'], filename, output.getvalue())
    path = Path(current_app.config['UPLOAD_FOLDER'])
    path.mkdir(parents=True, exist_ok=True)
    (path / filename).write_bytes(output.getvalue())
    return url_for('web.uploaded', filename=filename)


@bp.route('/imagenes/<filename>')
def uploaded(filename):
    if not re.fullmatch(r'[a-f0-9]{32}\.jpg', filename):
        abort(404)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@bp.route('/admin/deportes/nuevo', methods=['GET', 'POST'])
@bp.route('/admin/deportes/<identifier>/editar', methods=['GET', 'POST'])
@authenticated(admin=True)
def edit_sport(identifier=None):
    sport = sport_by_id(identifier, True) if identifier else None
    if request.method == 'POST':
        try:
            form = request.form
            row = {key: text(form, key, 1, 3000) for key in ('descripcion', 'equipamiento', 'consejos', 'alimentacion', 'condiciones', 'beneficios')}
            row.update(nombre=text(form, 'nombre', 2, 100),
                       objetivo=','.join(sorted(set(form.getlist('objetivo')))),
                       costo=float(money(number(form.get('costo'), 'Costo', 0, 100000))) if form.get('costo', '').strip() else None,
                       moneda='BOB', periodo='mes',
                       minutos=number(form.get('minutos'), 'Minutos', 10, 240, True),
                       espacio=choice(form.get('espacio'), ['interior', 'exterior', 'ambos'], 'espacio'),
                       dificultad=choice(form.get('dificultad'), ['basica', 'intermedia', 'alta'], 'dificultad'))
            if not row['objetivo'] or any(k not in GOALS for k in row['objetivo'].split(',')):
                raise ValueError('Selecciona al menos un objetivo válido.')
            file = request.files.get('imagen')
            if not sport and (not file or not file.filename):
                raise ValueError('Selecciona una imagen para el deporte.')
            if file and file.filename:
                row['imagen'] = upload_image(file)
            if sport:
                db().update('deportes', identifier, row)
            else:
                slug = re.sub(r'[^a-z0-9]+', '-', normalized(row['nombre'])).strip('-')[:60] or 'deporte'
                identifier = slug + '-' + uuid4().hex[:8]
                row.update(id=identifier, activo=True)
                db().add('deportes', row)
            flash('Deporte guardado correctamente.', 'success')
            return redirect(url_for('web.detail', identifier=identifier))
        except (ValueError, DataError) as error:
            flash(str(error) + ' Si elegiste una imagen, selecciónala nuevamente.', 'error')
            return render_template('sport_form.html', sport=sport, values=request.form), 400 if isinstance(error, ValueError) else 503
    return render_template('sport_form.html', sport=sport, values=sport or {})


@bp.post('/admin/deportes/<identifier>/<action>')
@authenticated(admin=True)
def availability(identifier, action):
    sport = sport_by_id(identifier, True)
    if action == 'estado':
        active = request.form.get('activo')
        if active not in ('0', '1'):
            abort(400)
        db().update('deportes', identifier, {'activo': active == '1'})
        flash('Disponibilidad actualizada.', 'success')
    elif action == 'eliminar':
        if request.form.get('confirmacion') != identifier:
            flash('Escribe el identificador exacto para confirmar la eliminación.', 'error')
            return redirect(url_for('web.admin'))
        try:
            db().delete('deportes', identifier)
            flash('Deporte eliminado.', 'success')
        except Conflict:
            flash('Este deporte tiene favoritos o reportes asociados. Desactívalo para conservar sus referencias.', 'error')
    else:
        abort(404)
    return redirect(url_for('web.admin'))


@bp.post('/admin/reportes/<identifier>')
@authenticated(admin=True)
def review_report(identifier):
    if not db().get('reportes', identifier):
        abort(404)
    state = request.form.get('estado')
    if state not in ('pendiente', 'resuelto', 'descartado'):
        abort(400)
    db().update('reportes', identifier, {'estado': state})
    flash('Estado del reporte actualizado.', 'success')
    return redirect(url_for('web.admin'))
