import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template

from .store import Store, DataError


def create_app(overrides=None):
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / '.env')
    app = Flask(__name__, instance_path=str(root / 'instance'))
    Path(app.instance_path).mkdir(exist_ok=True)
    keyfile = Path(app.instance_path) / 'session.key'
    if not keyfile.exists():
        try:
            with keyfile.open('x') as stream:
                stream.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY') or keyfile.read_text().strip(),
        DATABASE=str(Path(app.instance_path) / 'sportsinfo.sqlite3'),
        DATA_BACKEND=os.getenv('DATA_BACKEND', 'local'),
        SUPABASE_URL=os.getenv('SUPABASE_URL', ''),
        SUPABASE_SECRET_KEY=os.getenv('SUPABASE_SECRET_KEY', ''),
        SUPABASE_BUCKET=os.getenv('SPORTSINFO_BUCKET', 'sportsinfo-imagenes'),
        UPLOAD_FOLDER=str(Path(app.instance_path) / 'uploads'),
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE') == '1',
        PERMANENT_SESSION_LIFETIME=7200,
        SEED_LOCAL=True,
    )
    if overrides:
        app.config.update(overrides)
    if app.config['DATA_BACKEND'] not in ('local', 'supabase'):
        raise RuntimeError('DATA_BACKEND debe ser local o supabase.')
    store = Store(app.config)
    app.extensions['store'] = store
    app.extensions['login_attempts'] = {}
    if not store.remote and store.new_local and app.config['SEED_LOCAL']:
        from .seed import sports
        for row in sports():
            if not store.get('deportes', row['id']):
                store.add('deportes', row)
    from .routes import bp, csrf
    app.jinja_env.globals['csrf'] = csrf
    app.register_blueprint(bp)

    @app.errorhandler(DataError)
    def data_error(error):
        return render_template('error.html', title='Conexión no disponible', message=str(error)), 503

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def http_error(error):
        messages = {400: 'La solicitud no es válida. Actualiza la página y vuelve a intentarlo.',
                    403: 'Tu cuenta no tiene permiso para realizar esta acción.',
                    404: 'No encontramos esta página o el deporte solicitado.',
                    413: 'El archivo supera el tamaño permitido de 5 MB.'}
        return render_template('error.html', title=str(error.code), message=messages[error.code]), error.code

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        if response.mimetype == 'text/html':
            response.headers['Cache-Control'] = 'no-store'
        return response

    return app
