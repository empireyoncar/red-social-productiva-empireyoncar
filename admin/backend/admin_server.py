from flask import Flask, request, jsonify
from flask_cors import CORS
from db_usuarios import obtener_perfil, verificar_usuario_admin
from dbgrupos import get_db
import os

app = Flask(__name__)
CORS(app)

ADMIN_IP = "192.168.1.178"

# ============================================================
# RESTRICCIÓN DE ACCESO SOLO PARA ADMIN
# ============================================================

@app.before_request
def limitar_ip():
    client_ip = request.remote_addr
    if client_ip != ADMIN_IP:
        return jsonify({"error": "Acceso restringido al administrador"}), 403

# ============================================================
# DASHBOARD
# ============================================================

@app.get("/admin/dashboard")
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM usuarios")
    total_usuarios = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM grupos")
    total_grupos = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM posts_grupo")
    total_post_grupos = cur.fetchone()["total"]

    cur.close()
    conn.close()

    return jsonify({
        "usuarios": total_usuarios,
        "grupos": total_grupos,
        "posts_grupos": total_post_grupos
    })

# ============================================================
# GESTIÓN DE USUARIOS
# ============================================================

@app.get("/admin/usuarios")
def admin_usuarios():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, nombres, apellidos, email, verificado FROM usuarios")
    usuarios = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(usuarios)

@app.post("/admin/usuario/verificar")
def admin_verificar_usuario():
    data = request.get_json()
    user_id = data.get("user_id")
    return jsonify(verificar_usuario_admin(user_id))

@app.post("/admin/usuario/eliminar")
def admin_eliminar_usuario():
    data = request.get_json()
    user_id = data.get("user_id")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"status": "eliminado"})

# ============================================================
# GESTIÓN DE GRUPOS
# ============================================================

@app.get("/admin/grupos")
def admin_grupos():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM grupos")
    grupos = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(grupos)

@app.post("/admin/grupo/eliminar")
def admin_eliminar_grupo():
    data = request.get_json()
    grupo_id = data.get("grupo_id")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM grupos WHERE id = %s", (grupo_id,))
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"status": "grupo eliminado"})

# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5110, debug=True)
