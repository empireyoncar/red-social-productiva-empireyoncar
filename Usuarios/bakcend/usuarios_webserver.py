import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Clave de sesión (cámbiala en producción)
app.secret_key = os.environ.get("SECRET_KEY", "cambia_esta_clave_super_secreta")

# URL de la base de datos (docker-compose la pondrá)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://empireyoncar:empireyoncar@db:5432/empireyoncar_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# MODELOS
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(60), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


# RUTAS

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("navegacion"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        terms = request.form.get("terms")

        # Validaciones básicas
        if not all([full_name, username, email, password, confirm]):
            flash("Completa todos los campos.", "error")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for("register"))

        if not terms:
            flash("Debes aceptar los términos y condiciones.", "error")
            return redirect(url_for("register"))

        # Comprobar si existe usuario/correo
        if User.query.filter_by(username=username).first():
            flash("El nombre de usuario ya está en uso.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("El correo ya está registrado.", "error")
            return redirect(url_for("register"))

        # Crear usuario
        user = User(full_name=full_name, username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registro completado. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_input = request.form.get("user", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.username == user_input) | (User.email == user_input)
        ).first()

        if not user or not user.check_password(password):
            flash("Usuario o contraseña incorrectos.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session["username"] = user.username
        session["full_name"] = user.full_name

        return redirect(url_for("navegacion"))

    return render_template("login.html")


@app.route("/navegacion", methods=["GET", "POST"])
def navegacion():
    if "user_id" not in session:
        flash("Debes iniciar sesión.", "error")
        return redirect(url_for("login"))

    # Aquí más adelante podrás manejar publicaciones (texto, imagen, video)
    # Por ahora solo renderizamos la plantilla.
    return render_template("navegación.html")  # o "navegacion.html"


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for("login"))


# Crear tablas al arrancar (solo para desarrollo)
@app.before_first_request
def create_tables():
    db.create_all()


if __name__ == "__main__":
    # Para desarrollo local (fuera de Docker)
    app.run(host="0.0.0.0", port=6001, debug=True)