import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

DB_CONFIG = {
    "host": "postgres",
    "database": "empireyoncar",
    "user": "admin",
    "password": "admin123",
    "port": 5432
}

def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def init_admin_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    # Crear admin por defecto si no existe
    cur.execute("SELECT * FROM admin_users WHERE usuario = 'admin'")
    if not cur.fetchone():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cur.execute("INSERT INTO admin_users (usuario, password) VALUES (%s, %s)", ("admin", hashed))

    conn.commit()
    cur.close()
    conn.close()

def validar_admin(usuario, password):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM admin_users WHERE usuario = %s", (usuario,))
    admin = cur.fetchone()

    cur.close()
    conn.close()

    if not admin:
        return False

    return bcrypt.checkpw(password.encode(), admin["password"].encode())
