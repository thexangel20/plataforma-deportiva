import os

from flask import Flask

try:
    from dotenv import load_dotenv
except ImportError:  # Permite ejecutar el modo local sin dependencias opcionales.
    load_dotenv = None

if load_dotenv:
    load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "sportsinfo-development-key")

from app import routes
