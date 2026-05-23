import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from db_bootstrap import ensure_database
import os
import uuid

# ============================================================
# CONFIGURACIÓN DE POSTGRESQL
# ============================================================

DB_CONFIG = {
    "host": "postgres",
    "database": "usuarios_db",
    "user": "admin",
    "password": "admin123",
    "port": 5151
}

ensure_database(DB_CONFIG["database"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.environ.get("USER_UPLOAD_ROOT", os.path.join(BASE_DIR, "uploads"))
PROFILE_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "profiles")

os.makedirs(PROFILE_UPLOAD_DIR, exist_ok=True)

def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# ============================================================
# CREAR TABLA SI NO EXISTE
# ============================================================

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            nacimiento DATE NOT NULL,
            oficio TEXT,
            pais TEXT,
            estado TEXT,
            ciudad TEXT,
            whatsapp TEXT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            verificado BOOLEAN DEFAULT FALSE,
            seguidores INT DEFAULT 0,
            siguiendo INT DEFAULT 0,
            bio TEXT DEFAULT '',
            foto_url TEXT,
            last_seen TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS foto_url TEXT;")
    cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS follows (
            id SERIAL PRIMARY KEY,
            follower_id INT NOT NULL,
            followed_id INT NOT NULL,
            UNIQUE(follower_id, followed_id)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

# ============================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================

def registrar_usuario(data):
    nombres = data.get("nombres")
    apellidos = data.get("apellidos")
    nacimiento = data.get("nacimiento")
    oficio = data.get("oficio")
    pais = data.get("pais")
    estado = data.get("estado")
    ciudad = data.get("ciudad")
    whatsapp = data.get("whatsapp")
    email = data.get("email")
    password = data.get("password")

    if not all([nombres, apellidos, nacimiento, email, password]):
        return {"error": "Faltan campos obligatorios"}

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO usuarios 
            (nombres, apellidos, nacimiento, oficio, pais, estado, ciudad, whatsapp, email, password)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id;
        """, (nombres, apellidos, nacimiento, oficio, pais, estado, ciudad, whatsapp, email, hashed))

        user_id = cur.fetchone()["id"]
        conn.commit()

        return {"status": "ok", "user_id": user_id}

    except psycopg2.Error:
        conn.rollback()
        return {"error": "El correo ya está registrado"}

    finally:
        cur.close()
        conn.close()


def login_usuario(email, password):
    if not email or not password:
        return {"error": "Email y contraseña son obligatorios"}

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        return {"error": "Usuario no encontrado"}

    if bcrypt.checkpw(password.encode(), user["password"].encode()):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET last_seen = NOW() WHERE id = %s", (user["id"],))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok", "user_id": user["id"]}

    return {"error": "Contraseña incorrecta"}


def obtener_perfil(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombres, apellidos, nacimiento, oficio, pais, estado, ciudad,
               whatsapp, email, verificado, seguidores, siguiendo, bio, foto_url, last_seen
        FROM usuarios WHERE id = %s
    """, (user_id,))

    user = cur.fetchone()

    cur.close()
    conn.close()

    return user


def actualizar_bio(user_id, bio):
    if not user_id:
        return {"error": "user_id es obligatorio"}

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE usuarios SET bio = %s WHERE id = %s", (bio, user_id))
    conn.commit()

    cur.close()
    conn.close()

    return {"status": "ok"}


def actualizar_perfil(user_id, data):
    if not user_id:
        return {"error": "user_id es obligatorio"}

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE usuarios
        SET nombres = %s,
            apellidos = %s,
            oficio = %s,
            pais = %s,
            estado = %s,
            ciudad = %s,
            whatsapp = %s,
            bio = %s,
            last_seen = NOW()
        WHERE id = %s
    """, (
        data.get("nombres"),
        data.get("apellidos"),
        data.get("oficio"),
        data.get("pais"),
        data.get("estado"),
        data.get("ciudad"),
        data.get("whatsapp"),
        data.get("bio"),
        user_id,
    ))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "ok"}


def guardar_foto_perfil(user_id, file_storage):
    if not user_id or not file_storage or not file_storage.filename:
        return {"error": "Archivo requerido"}

    extension = os.path.splitext(file_storage.filename)[1].lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{extension}"
    final_path = os.path.join(PROFILE_UPLOAD_DIR, filename)
    file_storage.save(final_path)
    foto_url = f"/empireyoncarsocial/usuarios/api/perfil/foto/{filename}"

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET foto_url = %s, last_seen = NOW() WHERE id = %s", (foto_url, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "ok", "foto_url": foto_url}


def verificar_usuario_admin(user_id):
    if not user_id:
        return {"error": "user_id es obligatorio"}

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE usuarios SET verificado = TRUE WHERE id = %s", (user_id,))
    conn.commit()

    cur.close()
    conn.close()

    return {"status": "verificado"}


def buscar_usuarios(query, current_user_id=None):
    conn = get_db()
    cur = conn.cursor()
    like_value = f"%{query.strip()}%"
    cur.execute("""
        SELECT id, nombres, apellidos, oficio, ciudad, pais, foto_url, verificado, seguidores
        FROM usuarios
        WHERE (nombres ILIKE %s OR apellidos ILIKE %s)
          AND (%s IS NULL OR id <> %s)
        ORDER BY seguidores DESC, nombres ASC
        LIMIT 25
    """, (like_value, like_value, current_user_id, current_user_id))
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users


def seguir_usuario(follower_id, followed_id):
    if not follower_id or not followed_id or follower_id == followed_id:
        return {"error": "Solicitud invalida"}

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO follows (follower_id, followed_id)
            VALUES (%s, %s)
        """, (follower_id, followed_id))
        cur.execute("UPDATE usuarios SET siguiendo = siguiendo + 1 WHERE id = %s", (follower_id,))
        cur.execute("UPDATE usuarios SET seguidores = seguidores + 1 WHERE id = %s", (followed_id,))
        conn.commit()
    except psycopg2.Error:
        conn.rollback()
        cur.close()
        conn.close()
        return {"error": "Ya sigues a este usuario"}

    cur.close()
    conn.close()
    return {"status": "ok"}


def esta_siguiendo(follower_id, followed_id):
    if not follower_id or not followed_id:
        return False
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1
        FROM follows
        WHERE follower_id = %s AND followed_id = %s
    """, (follower_id, followed_id))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists
