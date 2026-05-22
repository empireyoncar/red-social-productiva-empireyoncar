import psycopg2
from psycopg2.extras import RealDictCursor
from db_bootstrap import ensure_database
from flask import Flask, request, jsonify
from flask_cors import CORS

DB_CONFIG = {
    "host": "postgres",
    "database": "posts_db",
    "user": "admin",
    "password": "admin123",
    "port": 5151
}

ensure_database(DB_CONFIG["database"])


def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts_grupo (
            id SERIAL PRIMARY KEY,
            grupo_id INT NOT NULL,
            user_id INT NOT NULL,
            contenido TEXT NOT NULL,
            imagen TEXT,
            fecha TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

app = Flask(__name__)
CORS(app)

# Inicializar BD (asegura que posts_grupo existe)
init_db()

# ============================================================
# CREAR POST EN UN GRUPO
# ============================================================

@app.post("/api/grupos/post/crear")
def crear_post_grupo():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    grupo_id = data.get("grupo_id")
    user_id = data.get("user_id")
    contenido = data.get("contenido")
    imagen = data.get("imagen")  # opcional

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO posts_grupo (grupo_id, user_id, contenido, imagen)
        VALUES (%s, %s, %s, %s)
        RETURNING id, fecha;
    """, (grupo_id, user_id, contenido, imagen))

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
# LISTAR POSTS DE UN GRUPO
# ============================================================

@app.get("/api/grupos/post/lista/<int:grupo_id>")
def lista_posts_grupo(grupo_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.*, u.nombres, u.apellidos, u.verificado
        FROM posts_grupo p
        JOIN usuarios u ON u.id = p.user_id
        WHERE grupo_id = %s
        ORDER BY fecha DESC;
    """, (grupo_id,))

    posts = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(posts)

# ============================================================
# ELIMINAR POST (solo dueño o admin del grupo)
# ============================================================

@app.post("/api/grupos/post/eliminar")
def eliminar_post_grupo():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    post_id = data.get("post_id")
    user_id = data.get("user_id")
    admin = data.get("admin", False)

    conn = get_db()
    cur = conn.cursor()

    # Obtener post
    cur.execute("SELECT * FROM posts_grupo WHERE id = %s", (post_id,))
    post = cur.fetchone()

    if not post:
        return jsonify({"error": "Post no existe"}), 404

    # Verificar si es dueño o admin
    if post["user_id"] != user_id and not admin:
        return jsonify({"error": "No autorizado"}), 403

    cur.execute("DELETE FROM posts_grupo WHERE id = %s", (post_id,))
    conn.commit()

    cur.close()
    conn.close()

    return jsonify({"status": "eliminado"})

# ============================================================
# EDITAR POST (opcional)
# ============================================================

@app.post("/api/grupos/post/editar")
def editar_post_grupo():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400

    post_id = data.get("post_id")
    user_id = data.get("user_id")
    contenido = data.get("contenido")
    imagen = data.get("imagen")

    conn = get_db()
    cur = conn.cursor()

    # Verificar dueño
    cur.execute("SELECT user_id FROM posts_grupo WHERE id = %s", (post_id,))
    post = cur.fetchone()

    if not post:
        return jsonify({"error": "Post no existe"}), 404

    if post["user_id"] != user_id:
        return jsonify({"error": "No autorizado"}), 403

    cur.execute("""
        UPDATE posts_grupo
        SET contenido = %s, imagen = %s
        WHERE id = %s
    """, (contenido, imagen, post_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "editado"})

# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5108, debug=True)
