from flask import Flask
from bot_runner import run_bot

app = Flask(__name__)

@app.route("/")
def home():
    run_bot()
    return "✅ Bot eseguito"

if __name__ == "__main__":
    app.run(debug=False, port=10000, host="0.0.0.0")
