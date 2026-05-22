import os
import sys

from flask import Flask, request, jsonify
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db_usuarios import (
    init_db,
    registrar_usuario,
    login_usuario,
    obtener_perfil,
    actualizar_bio,
    verificar_usuario_admin,
)

app = Flask(__name__)
CORS(app)

# Inicializar BD
init_db()

# ============================================================
# REGISTRO
# ============================================================

@app.post("/api/register")
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    result = registrar_usuario(data)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)

# ============================================================
# LOGIN
# ============================================================

@app.post("/api/login")
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    result = login_usuario(data.get("email"), data.get("password"))

    if "error" in result:
        return jsonify(result), 401

    return jsonify(result)

# ============================================================
# PERFIL
# ============================================================

@app.get("/api/perfil/<int:user_id>")
def perfil(user_id):
    user = obtener_perfil(user_id)

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify(user)

# ============================================================
# ACTUALIZAR BIO
# ============================================================

@app.post("/api/perfil/update_bio")
def update_bio():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    result = actualizar_bio(data.get("user_id"), data.get("bio"))
    return jsonify(result)

# ============================================================
# VERIFICAR USUARIO (ADMIN)
# ============================================================

@app.post("/api/admin/verificar")
def verificar_usuario():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    result = verificar_usuario_admin(data.get("user_id"))
    return jsonify(result)

# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5101, debug=True)
