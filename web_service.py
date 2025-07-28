from flask import Flask
from bot_core import analizza_partite

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Tennis pronto ✅"

@app.route("/run")
def run():
    analizza_partite()
    return "Analisi completata ✅", 200
