import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from db_bootstrap import ensure_database

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
            bio TEXT DEFAULT ''
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
        return {"status": "ok", "user_id": user["id"]}

    return {"error": "Contraseña incorrecta"}


def obtener_perfil(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombres, apellidos, nacimiento, oficio, pais, estado, ciudad,
               whatsapp, email, verificado, seguidores, siguiendo, bio
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
