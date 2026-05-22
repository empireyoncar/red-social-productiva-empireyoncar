import psycopg2
from psycopg2.extras import RealDictCursor
from db_bootstrap import ensure_database

DB_CONFIG = {
    "host": "postgres",
    "database": "chat_grupos_db",
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
        CREATE TABLE IF NOT EXISTS mensajes_grupo (
            id SERIAL PRIMARY KEY,
            grupo_id INT NOT NULL,
            user_id INT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT NOW(),
            leido BOOLEAN DEFAULT FALSE
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
