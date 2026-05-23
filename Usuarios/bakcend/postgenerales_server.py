import json
import os
import re
import uuid

import psycopg2
import requests
from psycopg2.extras import Json
from werkzeug.utils import secure_filename

from db_post import (
    create_comment,
    create_post_record,
    delete_post_record,
    get_poll_for_post,
    get_post_owner,
    list_comments,
    list_feed_posts,
    list_posts_by_user,
    register_like,
    register_poll_vote,
)

USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://usuario_server:5101")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.environ.get("POST_UPLOAD_ROOT", os.path.join(BASE_DIR, "uploads"))
UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "posts")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

os.makedirs(UPLOAD_DIR, exist_ok=True)


def extract_meta(html, *patterns):
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return None


def link_preview_service(url):
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


def fetch_user_profile(user_id):
    try:
        response = requests.get(
            f"{USER_SERVICE_URL}/api/perfil/{int(user_id)}",
            timeout=3,
        )
        if not response.ok:
            return {}
        return response.json() or {}
    except (requests.RequestException, ValueError):
        return {}


def enrich_with_user(post_or_comment):
    profile = fetch_user_profile(post_or_comment.get("user_id"))
    post_or_comment["nombres"] = profile.get("nombres") or "Usuario"
    post_or_comment["apellidos"] = profile.get("apellidos") or ""
    post_or_comment["verificado"] = bool(profile.get("verificado"))
    return post_or_comment


def build_post_payload(data, files=None):
    try:
        user_id = int(data.get("user_id"))
    except (TypeError, ValueError):
        return None, ("user_id invalido", 400)

    contenido = (data.get("contenido") or "").strip()
    link_url = (data.get("link_url") or "").strip()
    link_title = (data.get("link_title") or "").strip()
    link_description = (data.get("link_description") or "").strip()
    link_image = (data.get("link_image") or "").strip()
    poll_question = (data.get("poll_question") or "").strip()
    poll_options = parse_poll_options(data.get("poll_options"))
    poll_votes = [0] * len(poll_options) if poll_options else None

    imagen = None
    if files and "imagen_archivo" in files:
        try:
            imagen = save_uploaded_image(files["imagen_archivo"])
        except ValueError as exc:
            return None, (str(exc), 400)
    else:
        imagen = (data.get("imagen") or "").strip() or None

    if link_url and not link_title and not link_description and not link_image:
        metadata = link_preview_service(link_url)
        link_title = metadata["title"] or ""
        link_description = metadata["description"] or ""
        link_image = metadata["image"] or ""

    if poll_question and len(poll_options) < 2:
        return None, ("La encuesta necesita al menos 2 opciones", 400)

    if not any([contenido, imagen, link_url, poll_question]):
        return None, ("Debes agregar texto, imagen, enlace o encuesta", 400)

    return {
        "user_id": user_id,
        "contenido": contenido,
        "imagen": imagen,
        "link_url": link_url or None,
        "link_title": link_title or None,
        "link_description": link_description or None,
        "link_image": link_image or None,
        "poll_question": poll_question or None,
        "poll_options": poll_options or None,
        "poll_votes": poll_votes or None,
    }, None


def create_post_service(data, files=None):
    payload, error = build_post_payload(data, files)
    if error:
        return {"error": error[0]}, error[1]

    post = create_post_record(payload, Json)
    return {
        "status": "ok",
        "post_id": post["id"],
        "fecha": post["fecha"],
    }, 200


def get_user_posts_service(user_id):
    return list_posts_by_user(user_id)


def feed_service(user_id):
    del user_id
    posts = list_feed_posts()
    return [enrich_with_user(post) for post in posts]


def vote_poll_service(data):
    try:
        user_id = int(data.get("user_id"))
        post_id = int(data.get("post_id"))
        option_index = int(data.get("option_index"))
    except (TypeError, ValueError):
        return {"error": "Datos invalidos"}, 400

    post = get_poll_for_post(post_id)
    if not post or not post["poll_options"]:
        return {"error": "Encuesta no encontrada"}, 404

    options = post["poll_options"]
    votes = post["poll_votes"] or [0] * len(options)
    if option_index < 0 or option_index >= len(options):
        return {"error": "Opcion invalida"}, 400

    votes[option_index] = int(votes[option_index]) + 1
    try:
        register_poll_vote(post_id, user_id, option_index, votes, Json)
    except psycopg2.Error:
        return {"error": "Ya votaste en esta encuesta"}, 400

    return {"status": "ok", "poll_votes": votes}, 200


def like_post_service(data):
    try:
        register_like(data.get("user_id"), data.get("post_id"))
    except psycopg2.Error:
        return {"error": "Ya diste like"}, 400
    return {"status": "ok"}, 200


def create_comment_service(data):
    comentario_db = create_comment(
        data.get("post_id"),
        data.get("user_id"),
        data.get("comentario"),
    )
    return {
        "status": "ok",
        "comentario_id": comentario_db["id"],
        "fecha": comentario_db["fecha"],
    }, 200


def get_comments_service(post_id):
    comentarios = list_comments(post_id)
    return [enrich_with_user(comentario) for comentario in comentarios]


def delete_post_service(data):
    post_id = data.get("post_id")
    user_id = data.get("user_id")
    admin = data.get("admin", False)

    post = get_post_owner(post_id)
    if not post:
        return {"error": "Post no existe"}, 404

    if post["user_id"] != user_id and not admin:
        return {"error": "No autorizado"}, 403

    delete_post_record(post_id)
    return {"status": "eliminado"}, 200
