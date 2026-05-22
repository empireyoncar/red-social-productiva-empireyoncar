from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# RUTA DEL FRONTEND DE GRUPOS
# ============================================================

GRUPOS_FRONTEND_PATH = "/app/Usuarios/frontend"

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(GRUPOS_FRONTEND_PATH)
])

# ============================================================
# RUTAS DEL FRONTEND
# ============================================================

@app.route("/grupos")
def grupos():
    return render_template("grupos.html")

@app.route("/solicitud-grupo")
def solicitud_grupo():
    return render_template("solicituddegrupos.html")

@app.route("/aprobar-miembro")
def aprobar_miembro():
    return render_template("aprobarmiembrogrupo.html")

@app.route("/")
def index():
    return render_template("grupos.html")

# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(GRUPOS_FRONTEND_PATH, "static"), filename)

# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5106, debug=True)
