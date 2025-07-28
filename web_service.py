from flask import Flask
from bot_runner import run_bot

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    run_bot()
    return "Bot eseguito con successo!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)