from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from jinja2 import FileSystemLoader, ChoiceLoader
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PATH = os.environ.get(
    "FRONTEND_PATH",
    os.path.normpath(os.path.join(BASE_DIR, "..", "frontend")),
)
THEME_PATH = os.environ.get(
    "THEME_PATH",
    os.path.normpath(os.path.join(BASE_DIR, "..", "..", "shared", "frontend")),
)

app.jinja_loader = ChoiceLoader([FileSystemLoader(FRONTEND_PATH)])


@app.route("/")
def index():
    return render_template("grupos.html")


@app.route("/grupos")
@app.route("/grupos/")
@app.route("/empireyoncarsocial/grupos")
@app.route("/empireyoncarsocial/grupos/")
def grupos():
    return render_template("grupos.html")


@app.route("/solicitud-grupo")
@app.route("/empireyoncarsocial/grupos/solicitud-grupo")
def solicitud_grupo():
    return render_template("solicituddegrupos.html")


@app.route("/aprobar-miembro")
@app.route("/empireyoncarsocial/grupos/aprobar-miembro")
def aprobar_miembro():
    return render_template("aprobarmiembrogrupo.html")


@app.route("/chat-grupo")
@app.route("/empireyoncarsocial/grupos/chat-grupo")
def chat_grupo():
    return render_template("chatgrupost.html")


@app.route("/grupo")
@app.route("/empireyoncarsocial/grupos/grupo")
def grupo_post():
    return render_template("grupospost.html")


@app.route("/miembros-grupo")
@app.route("/empireyoncarsocial/grupos/miembros-grupo")
def miembros_grupo():
    return render_template("miembrosdegrupo.html")


@app.route("/grupo-admin")
@app.route("/empireyoncarsocial/grupos/grupo-admin")
def grupo_admin():
    return render_template("gruposadmin.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(FRONTEND_PATH, "static"), filename)


@app.route("/theme.css")
def theme_css():
    return send_from_directory(THEME_PATH, "empireyoncar-theme.css")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5106, debug=True)
