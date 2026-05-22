from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# RUTA DEL FRONTEND DEL CHAT
# ============================================================

CHAT_FRONTEND_PATH = "/app/chat_frontend"

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(CHAT_FRONTEND_PATH)
])

# ============================================================
# RUTAS DEL FRONTEND
# ============================================================

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/")
def index():
    return render_template("chat.html")

# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(CHAT_FRONTEND_PATH, "static"), filename)

# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5103, debug=True)
