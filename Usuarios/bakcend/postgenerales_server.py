from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from db_bootstrap import ensure_database
from werkzeug.utils import secure_filename
import json
import os
import re
import uuid
from urllib.parse import urlparse
import requests

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host": "postgres",
    "database": "posts_db",
    "user": "admin",
    "password": "admin123",
    "port": 5151
}

ensure_database(DB_CONFIG["database"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.environ.get("POST_UPLOAD_ROOT", os.path.join(BASE_DIR, "uploads"))
UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "posts")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def extract_meta(html, *patterns):
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return None


def fetch_link_preview(url):
    try:
        response = requests.get(
            url,
            timeout=4,
            headers={"User-Agent": "EmpireyoncarSocialBot/1.0"},
        )
        response.raise_for_status()
        html = response.text[:200000]
    except requests.RequestException:
        return {"url": url, "title": None, "description": None, "image": None}

    return {
        "url": url,
        "title": extract_meta(
            html,
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
            r"<title>(.*?)</title>",
        ),
        "description": extract_meta(
            html,
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        ),
        "image": extract_meta(
            html,
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        ),
    }


def save_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    parsed_name = secure_filename(file_storage.filename)
    _, ext = os.path.splitext(parsed_name.lower())
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Formato de imagen no permitido")

    filename = f"{uuid.uuid4().hex}{ext}"
    final_path = os.path.join(UPLOAD_DIR, filename)
    file_storage.save(final_path)
    return f"/empireyoncarsocial/posts_api/uploads/{filename}"


def parse_poll_options(raw_options):
    if not raw_options:
        return []
    if isinstance(raw_options, list):
        options = raw_options
    else:
        try:
            options = json.loads(raw_options)
        except json.JSONDecodeError:
            options = []
    clean_options = [str(option).strip() for option in options if str(option).strip()]
    return clean_options[:4]


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            contenido TEXT NOT NULL DEFAULT '',
            imagen TEXT,
            fecha TIMESTAMP DEFAULT NOW(),
            likes INT DEFAULT 0,
            link_url TEXT,
            link_title TEXT,
            link_description TEXT,
            link_image TEXT,
            poll_question TEXT,
            poll_options JSONB,
            poll_votes JSONB
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL,
            post_id INT NOT NULL,
            UNIQUE(user_id, post_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS comentarios (
            id SERIAL PRIMARY KEY,
            post_id INT NOT NULL,
            user_id INT NOT NULL,
            comentario TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS poll_responses (
            id SERIAL PRIMARY KEY,
            post_id INT NOT NULL,
            user_id INT NOT NULL,
            option_index INT NOT NULL,
            UNIQUE(post_id, user_id)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


init_db()


@app.get("/uploads/<path:filename>")
def uploaded_post_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.post("/api/post/link-preview")
def link_preview():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "URL requerida"}), 400

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return jsonify({"error": "URL invalida"}), 400

    return jsonify(fetch_link_preview(url))


@app.post("/api/post/crear")
def crear_post():
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    data = request.form if is_multipart else (request.get_json(silent=True) or {})
    if not data:
        return jsonify({"error": "Solicitud vacia"}), 400

    try:
        user_id = int(data.get("user_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "user_id invalido"}), 400

    contenido = (data.get("contenido") or "").strip()
    link_url = (data.get("link_url") or "").strip()
    link_title = (data.get("link_title") or "").strip()
    link_description = (data.get("link_description") or "").strip()
    link_image = (data.get("link_image") or "").strip()
    poll_question = (data.get("poll_question") or "").strip()
    poll_options = parse_poll_options(data.get("poll_options"))
    poll_votes = [0] * len(poll_options) if poll_options else None

    imagen = None
    if is_multipart and "imagen_archivo" in request.files:
        try:
            imagen = save_uploaded_image(request.files["imagen_archivo"])
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
    else:
        imagen = (data.get("imagen") or "").strip() or None

    if link_url and not link_title and not link_description and not link_image:
        metadata = fetch_link_preview(link_url)
        link_title = metadata["title"] or ""
        link_description = metadata["description"] or ""
        link_image = metadata["image"] or ""

    if poll_question and len(poll_options) < 2:
        return jsonify({"error": "La encuesta necesita al menos 2 opciones"}), 400

    if not any([contenido, imagen, link_url, poll_question]):
        return jsonify({"error": "Debes agregar texto, imagen, enlace o encuesta"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO posts (
            user_id, contenido, imagen, link_url, link_title,
            link_description, link_image, poll_question, poll_options, poll_votes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, fecha;
    """, (
        user_id,
        contenido,
        imagen,
        link_url or None,
        link_title or None,
        link_description or None,
        link_image or None,
        poll_question or None,
        Json(poll_options) if poll_options else None,
        Json(poll_votes) if poll_votes else None,
    ))

    post = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "status": "ok",
        "post_id": post["id"],
        "fecha": post["fecha"]
    })


@app.get("/api/post/usuario/<int:user_id>")
def posts_usuario(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM posts
        WHERE user_id = %s
        ORDER BY fecha DESC;
    """, (user_id,))

    posts = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(posts)


@app.get("/api/post/feed/<int:user_id>")
def feed(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.*, u.nombres, u.apellidos, u.verificado
        FROM posts p
        JOIN usuarios u ON u.id = p.user_id
        ORDER BY p.fecha DESC
        LIMIT 50;
    """)

    posts = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(posts)


@app.post("/api/post/poll/vote")
def votar_encuesta():
    data = request.get_json(silent=True) or {}

    try:
        user_id = int(data.get("user_id"))
        post_id = int(data.get("post_id"))
        option_index = int(data.get("option_index"))
    except (TypeError, ValueError):
        return jsonify({"error": "Datos invalidos"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT poll_options, poll_votes FROM posts WHERE id = %s", (post_id,))
    post = cur.fetchone()
    if not post or not post["poll_options"]:
        cur.close()
        conn.close()
        return jsonify({"error": "Encuesta no encontrada"}), 404

    options = post["poll_options"]
    votes = post["poll_votes"] or [0] * len(options)
    if option_index < 0 or option_index >= len(options):
        cur.close()
        conn.close()
        return jsonify({"error": "Opcion invalida"}), 400

    try:
        cur.execute("""
            INSERT INTO poll_responses (post_id, user_id, option_index)
            VALUES (%s, %s, %s)
        """, (post_id, user_id, option_index))
    except psycopg2.Error:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": "Ya votaste en esta encuesta"}), 400

    votes[option_index] = int(votes[option_index]) + 1
    cur.execute(
        "UPDATE posts SET poll_votes = %s WHERE id = %s",
        (Json(votes), post_id),
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok", "poll_votes": votes})


@app.post("/api/post/like")
def like_post():
    data = request.get_json(silent=True) or {}

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
            UPDATE posts
            SET likes = likes + 1
            WHERE id = %s
        """, (post_id,))

        conn.commit()
    except psycopg2.Error:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": "Ya diste like"}), 400

    cur.close()
    conn.close()

    return jsonify({"status": "ok"})


@app.post("/api/post/comentar")
def comentar_post():
    data = request.get_json(silent=True) or {}

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

    comentario_db = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "status": "ok",
        "comentario_id": comentario_db["id"],
        "fecha": comentario_db["fecha"]
    })


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


@app.post("/api/post/eliminar")
def eliminar_post():
    data = request.get_json(silent=True) or {}

    post_id = data.get("post_id")
    user_id = data.get("user_id")
    admin = data.get("admin", False)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
    post = cur.fetchone()

    if not post:
        cur.close()
        conn.close()
        return jsonify({"error": "Post no existe"}), 404

    if post["user_id"] != user_id and not admin:
        cur.close()
        conn.close()
        return jsonify({"error": "No autorizado"}), 403

    cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "eliminado"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5104, debug=True)
