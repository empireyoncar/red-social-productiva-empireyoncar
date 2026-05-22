from flask import Flask, request, jsonify
from flask_cors import CORS
from db_admin import init_admin_db, validar_admin
import secrets

app = Flask(__name__)
CORS(app)

ADMIN_IP = "192.168.1.178"
TOKENS_VALIDOS = {}

init_admin_db()

# ============================================================
# RESTRICCIÓN DE IP
# ============================================================

@app.before_request
def limitar_ip():
    if request.remote_addr != ADMIN_IP:
        return jsonify({"error": "Acceso restringido al administrador"}), 403

# ============================================================
# LOGIN ADMIN
# ============================================================

@app.post("/admin/login")
def admin_login():
    data = request.get_json()
    usuario = data.get("usuario")
    password = data.get("password")

    if validar_admin(usuario, password):
        token = secrets.token_hex(32)
        TOKENS_VALIDOS[token] = usuario
        return jsonify({"status": "ok", "token": token})

    return jsonify({"error": "Credenciales incorrectas"}), 401

# ============================================================
# VALIDAR TOKEN
# ============================================================

@app.post("/admin/validar")
def validar():
    data = request.get_json()
    token = data.get("token")

    if token in TOKENS_VALIDOS:
        return jsonify({"status": "ok"})

    return jsonify({"error": "Token inválido"}), 403

# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5109, debug=True)
