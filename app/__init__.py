from flask import Flask


app = Flask(__name__)

app.secret_key = "sportsinfo-clave-desarrollo"


from app import routes