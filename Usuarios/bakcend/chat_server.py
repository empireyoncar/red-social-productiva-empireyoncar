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
    "database": "chat_db",
    "user": "admin",
    "password": "admin123",
    "port": 5151
}

ensure_database(DB_CONFIG["database"])

def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# ============================================================
# CREAR TABLAS SI NO EXISTEN
# ============================================================

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Tabla de mensajes privados
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id SERIAL PRIMARY KEY,
            emisor INT NOT NULL,
            receptor INT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT NOW(),
            leido BOOLEAN DEFAULT FALSE
        );
    """)

    # Tabla para notificaciones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notificaciones (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            tipo TEXT NOT NULL,
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
# ENVIAR MENSAJE PRIVADO
# ============================================================

@app.post("/api/chat/enviar")
def enviar_mensaje():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    emisor = data.get("emisor")
    receptor = data.get("receptor")
    mensaje = data.get("mensaje")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO mensajes (emisor, receptor, mensaje)
        VALUES (%s, %s, %s)
        RETURNING id, fecha;
    """, (emisor, receptor, mensaje))

    msg = cur.fetchone()

    # Crear notificación
    cur.execute("""
        INSERT INTO notificaciones (user_id, tipo, contenido)
        VALUES (%s, 'mensaje', %s)
    """, (receptor, f"Nuevo mensaje de usuario {emisor}"))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "status": "ok",
        "mensaje_id": msg["id"],
        "fecha": msg["fecha"]
    })

# ============================================================
# OBTENER CONVERSACIÓN ENTRE DOS USUARIOS
# ============================================================

@app.get("/api/chat/conversacion/<int:u1>/<int:u2>")
def obtener_conversacion(u1, u2):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM mensajes
        WHERE (emisor = %s AND receptor = %s)
           OR (emisor = %s AND receptor = %s)
        ORDER BY fecha ASC;
    """, (u1, u2, u2, u1))

    mensajes = cur.fetchall()

    # Marcar como leídos los mensajes recibidos
    cur.execute("""
        UPDATE mensajes
        SET leido = TRUE
        WHERE receptor = %s AND emisor = %s;
    """, (u1, u2))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(mensajes)

# ============================================================
# LISTA DE CHATS (último mensaje por usuario)
# ============================================================

@app.get("/api/chat/lista/<int:user_id>")
def lista_chats(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT ON (otro)
            id, emisor, receptor, mensaje, fecha, leido,
            CASE 
                WHEN emisor = %s THEN receptor
                ELSE emisor
            END AS otro
        FROM (
            SELECT *
            FROM mensajes
            WHERE emisor = %s OR receptor = %s
            ORDER BY fecha DESC
        ) AS sub
        ORDER BY otro, fecha DESC;
    """, (user_id, user_id, user_id))

    chats = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(chats)

# ============================================================
# NOTIFICACIONES DEL USUARIO
# ============================================================

@app.get("/api/chat/notificaciones/<int:user_id>")
def notificaciones(user_id):
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
# MARCAR NOTIFICACIONES COMO LEÍDAS
# ============================================================

@app.post("/api/chat/notificaciones/leido")
def marcar_notificaciones():
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
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5102, debug=True)
