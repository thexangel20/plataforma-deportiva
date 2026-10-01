from flask import Flask

try:
    from dotenv import load_dotenv
except ImportError:  # Permite ejecutar el modo local sin dependencias opcionales.
    load_dotenv = None

if load_dotenv:
    load_dotenv()

app = Flask(__name__)

from app import routes
