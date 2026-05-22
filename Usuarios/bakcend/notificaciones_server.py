from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from db_bootstrap import ensure_database

app = Flask(__name__)
CORS(app)

# ============================================================
# CONFIG POSTGRESQL
# ============================================================

DB_CONFIG = {
    "host": "postgres",
    "database": "notificaciones_db",
    "user": "admin",
    "password": "admin123",
    "port": 5151
}

ensure_database(DB_CONFIG["database"])

def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# ============================================================
# CREAR TABLA SI NO EXISTE
# ============================================================

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notificaciones (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            tipo TEXT NOT NULL,           -- mensaje, like, comentario, grupo, sistema
            contenido TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT NOW(),
            leido BOOLEAN DEFAULT FALSE
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ============================================================
# CREAR NOTIFICACIÓN
# ============================================================

@app.post("/api/notificaciones/crear")
def crear_notificacion():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    user_id = data.get("user_id")
    tipo = data.get("tipo")
    contenido = data.get("contenido")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO notificaciones (user_id, tipo, contenido)
        VALUES (%s, %s, %s)
        RETURNING id, fecha;
    """, (user_id, tipo, contenido))

    notif = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "status": "ok",
        "notificacion_id": notif["id"],
        "fecha": notif["fecha"]
    })

# ============================================================
# OBTENER NOTIFICACIONES DEL USUARIO
# ============================================================

@app.get("/api/notificaciones/<int:user_id>")
def obtener_notificaciones(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM notificaciones
        WHERE user_id = %s
        ORDER BY fecha DESC;
    """, (user_id,))

    notifs = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(notifs)

# ============================================================
# MARCAR TODAS COMO LEÍDAS
# ============================================================

@app.post("/api/notificaciones/marcar_leidas")
def marcar_leidas():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    user_id = data.get("user_id")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE notificaciones
        SET leido = TRUE
        WHERE user_id = %s;
    """, (user_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok"})

# ============================================================
# ELIMINAR UNA NOTIFICACIÓN
# ============================================================

@app.post("/api/notificaciones/eliminar")
def eliminar_notificacion():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    notif_id = data.get("notif_id")
    user_id = data.get("user_id")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM notificaciones
        WHERE id = %s AND user_id = %s;
    """, (notif_id, user_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "eliminado"})

# ============================================================
# ELIMINAR TODAS LAS NOTIFICACIONES
# ============================================================

@app.post("/api/notificaciones/eliminar_todas")
def eliminar_todas():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    user_id = data.get("user_id")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM notificaciones
        WHERE user_id = %s;
    """, (user_id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "todas eliminadas"})

# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5105, debug=True)
