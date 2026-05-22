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

app.jinja_loader = ChoiceLoader([FileSystemLoader(FRONTEND_PATH)])


@app.route("/")
def index():
    return render_template("grupos.html")


@app.route("/grupos")
def grupos():
    return render_template("grupos.html")


@app.route("/solicitud-grupo")
def solicitud_grupo():
    return render_template("solicituddegrupos.html")


@app.route("/aprobar-miembro")
def aprobar_miembro():
    return render_template("aprobarmiembrogrupo.html")


@app.route("/chat-grupo")
def chat_grupo():
    return render_template("chatgrupost.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(FRONTEND_PATH, "static"), filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5106, debug=True)
