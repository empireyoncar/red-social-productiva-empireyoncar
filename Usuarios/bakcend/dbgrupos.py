import psycopg2
from psycopg2.extras import RealDictCursor
from db_bootstrap import ensure_database

DB_CONFIG = {
    "host": "postgres",
    "database": "grupos_db",
    "user": "admin",
    "password": "admin123",
    "port": 5432
}

ensure_database(DB_CONFIG["database"])


def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS grupos (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            imagen TEXT,
            admin_id INT NOT NULL,
            fecha TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS miembros_grupo (
            id SERIAL PRIMARY KEY,
            grupo_id INT NOT NULL,
            user_id INT NOT NULL,
            rol TEXT DEFAULT 'miembro',
            UNIQUE(grupo_id, user_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes_grupo (
            id SERIAL PRIMARY KEY,
            grupo_id INT NOT NULL,
            user_id INT NOT NULL,
            fecha TIMESTAMP DEFAULT NOW(),
            estado TEXT DEFAULT 'pendiente'
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
