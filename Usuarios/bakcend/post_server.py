from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from urllib.parse import urlparse

from db_post import init_db
from postgenerales_server import (
    UPLOAD_DIR,
    create_comment_service,
    create_post_service,
    delete_comment_service,
    delete_post_service,
    feed_service,
    get_comments_service,
    get_user_posts_service,
    like_post_service,
    link_preview_service,
    update_comment_service,
    update_post_service,
    vote_poll_service,
)

app = Flask(__name__)
CORS(app)

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

    return jsonify(link_preview_service(url))


@app.post("/api/post/crear")
def crear_post():
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    data = request.form if is_multipart else (request.get_json(silent=True) or {})
    if not data:
        return jsonify({"error": "Solicitud vacia"}), 400

    result, status_code = create_post_service(data, request.files if is_multipart else None)
    return jsonify(result), status_code


@app.post("/api/post/editar")
def editar_post():
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    data = request.form if is_multipart else (request.get_json(silent=True) or {})
    if not data:
        return jsonify({"error": "Solicitud vacia"}), 400

    result, status_code = update_post_service(data, request.files if is_multipart else None)
    return jsonify(result), status_code


@app.get("/api/post/usuario/<int:user_id>")
def posts_usuario(user_id):
    return jsonify(get_user_posts_service(user_id))


@app.get("/api/post/feed/<int:user_id>")
def feed(user_id):
    return jsonify(feed_service(user_id))


@app.post("/api/post/poll/vote")
def votar_encuesta():
    data = request.get_json(silent=True) or {}
    result, status_code = vote_poll_service(data)
    return jsonify(result), status_code


@app.post("/api/post/like")
def like_post():
    data = request.get_json(silent=True) or {}
    result, status_code = like_post_service(data)
    return jsonify(result), status_code


@app.post("/api/post/comentar")
def comentar_post():
    data = request.get_json(silent=True) or {}
    result, status_code = create_comment_service(data)
    return jsonify(result), status_code


@app.get("/api/post/comentarios/<int:post_id>")
def obtener_comentarios(post_id):
    return jsonify(get_comments_service(post_id))


@app.post("/api/post/comentario/editar")
def editar_comentario():
    data = request.get_json(silent=True) or {}
    result, status_code = update_comment_service(data)
    return jsonify(result), status_code


@app.post("/api/post/comentario/eliminar")
def eliminar_comentario():
    data = request.get_json(silent=True) or {}
    result, status_code = delete_comment_service(data)
    return jsonify(result), status_code


@app.post("/api/post/eliminar")
def eliminar_post():
    data = request.get_json(silent=True) or {}
    result, status_code = delete_post_service(data)
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5104, debug=True)
