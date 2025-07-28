from flask import Flask
from bot_runner import run_bot

app = Flask(__name__)

@app.route("/")
def home():
    run_bot()
    return "✅ Bot eseguito"

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))  # Render assegna dinamicamente la porta in PORT
    app.run(host="0.0.0.0", port=port)

