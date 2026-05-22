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
    "database": "posts_db",
    "user": "admin",
    "password": "admin123",
    "port": 5432
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

    # Tabla de posts
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            contenido TEXT NOT NULL,
            imagen TEXT,
            fecha TIMESTAMP DEFAULT NOW(),
            likes INT DEFAULT 0
        );
    """)

    # Tabla de likes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            post_id INT NOT NULL,
            UNIQUE(user_id, post_id)
        );
    """)

    # Tabla de comentarios
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comentarios (
            id SERIAL PRIMARY KEY,
            post_id INT NOT NULL,
            user_id INT NOT NULL,
            comentario TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ============================================================
# CREAR POST
# ============================================================

@app.post("/api/post/crear")
def crear_post():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    user_id = data.get("user_id")
    contenido = data.get("contenido")
    imagen = data.get("imagen")  # puede ser URL o ruta

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO posts (user_id, contenido, imagen)
        VALUES (%s, %s, %s)
        RETURNING id, fecha;
    """, (user_id, contenido, imagen))

    post = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "status": "ok",
        "post_id": post["id"],
        "fecha": post["fecha"]
    })

# ============================================================
# OBTENER POSTS DEL USUARIO
# ============================================================

@app.get("/api/post/usuario/<int:user_id>")
def posts_usuario(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM posts
        WHERE user_id = %s
        ORDER BY fecha DESC;
    """, (user_id,))

    posts = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(posts)

# ============================================================
# OBTENER FEED (SEGUIDORES + RELEVANTES)
# ============================================================

@app.get("/api/post/feed/<int:user_id>")
def feed(user_id):
    conn = get_db()
    cur = conn.cursor()

    # Feed básico: todos los posts ordenados por fecha
    # (Luego se puede mejorar con seguidores)
    cur.execute("""
        SELECT p.*, u.nombres, u.apellidos, u.verificado
        FROM posts p
        JOIN usuarios u ON u.id = p.user_id
        ORDER BY fecha DESC
        LIMIT 50;
    """)

    posts = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(posts)

# ============================================================
# DAR LIKE
# ============================================================

@app.post("/api/post/like")
def like_post():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    user_id = data.get("user_id")
    post_id = data.get("post_id")

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO likes (user_id, post_id)
            VALUES (%s, %s)
        """, (user_id, post_id))

        cur.execute("""
            UPDATE posts SET likes = likes + 1
            WHERE id = %s
        """, (post_id,))

        conn.commit()

    except psycopg2.Error:
        conn.rollback()
        return jsonify({"error": "Ya diste like"}), 400

    cur.close()
    conn.close()

    return jsonify({"status": "ok"})

# ============================================================
# COMENTAR POST
# ============================================================

@app.post("/api/post/comentar")
def comentar_post():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    post_id = data.get("post_id")
    user_id = data.get("user_id")
    comentario = data.get("comentario")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO comentarios (post_id, user_id, comentario)
        VALUES (%s, %s, %s)
        RETURNING id, fecha;
    """, (post_id, user_id, comentario))

    com = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "status": "ok",
        "comentario_id": com["id"],
        "fecha": com["fecha"]
    })

# ============================================================
# OBTENER COMENTARIOS DE UN POST
# ============================================================

@app.get("/api/post/comentarios/<int:post_id>")
def obtener_comentarios(post_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.*, u.nombres, u.apellidos
        FROM comentarios c
        JOIN usuarios u ON u.id = c.user_id
        WHERE post_id = %s
        ORDER BY fecha ASC;
    """, (post_id,))

    comentarios = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(comentarios)

# ============================================================
# ELIMINAR POST (solo dueño o admin)
# ============================================================

@app.post("/api/post/eliminar")
def eliminar_post():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    post_id = data.get("post_id")
    user_id = data.get("user_id")
    admin = data.get("admin", False)

    conn = get_db()
    cur = conn.cursor()

    # Verificar dueño
    cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
    post = cur.fetchone()

    if not post:
        return jsonify({"error": "Post no existe"}), 404

    if post["user_id"] != user_id and not admin:
        return jsonify({"error": "No autorizado"}), 403

    cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"status": "eliminado"})

# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5104, debug=True)
