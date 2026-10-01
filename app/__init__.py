import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

load_dotenv(Path(__file__).resolve().parent.parent / '.env')
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY') or secrets.token_hex(32),
    SUPABASE_URL=os.getenv('SUPABASE_URL', '').rstrip('/'),
    SUPABASE_SECRET_KEY=os.getenv('SUPABASE_SECRET_KEY', ''),
    SUPABASE_BUCKET=os.getenv('SUPABASE_BUCKET', 'imagenes-deportes-axel'),
    ADMIN_USUARIO=os.getenv('ADMIN_USUARIO', ''),
    ADMIN_PASSWORD_HASH=os.getenv('ADMIN_PASSWORD_HASH', ''),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    MAX_CONTENT_LENGTH=6 * 1024 * 1024,
)

from app import routes, reportes, deportes, comparacion
