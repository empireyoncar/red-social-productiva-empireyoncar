from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# Cargar plantillas desde /Usuarios/frontend
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PATH = os.environ.get(
    "FRONTEND_PATH",
    os.path.normpath(os.path.join(BASE_DIR, "..", "frontend")),
)
THEME_PATH = os.environ.get(
    "THEME_PATH",
    os.path.normpath(os.path.join(BASE_DIR, "..", "..", "shared", "frontend")),
)

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(FRONTEND_PATH)
])

# ============================================================
# RUTAS DEL FRONTEND
# ============================================================


@app.route("/")
def index():
    return render_template("login.html")


@app.route("empireyoncarsocial/login")
def login():
    return render_template("login.html")


@app.route("empireyoncarsocial/register")
def register():
    return render_template("register.html")


@app.route("empireyoncarsocial/home")
def home():
    return render_template("home.html")


@app.route("empireyoncarsocial/perfil")
def perfil():
    return render_template("perfil.html")


# ============================================================
# ARCHIVOS ESTATICOS (CSS, JS, IMAGENES)
# ============================================================


@app.route("/static/<path:filename>")
def static_files(filename):
    static_dir = os.path.join(FRONTEND_PATH, "static")
    return send_from_directory(static_dir, filename)


@app.route("/theme.css")
def theme_css():
    return send_from_directory(THEME_PATH, "empireyoncar-theme.css")


# ============================================================
# INICIAR SERVIDOR
# ============================================================


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100, debug=True)
