import psycopg2

POSTGRES_ADMIN_CONFIG = {
    "host": "postgres",
    "database": "postgres",
    "user": "admin",
    "password": "admin123",
    "port": 5432,
}


def ensure_database(db_name):
    conn = psycopg2.connect(**POSTGRES_ADMIN_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{db_name}"')
    cur.close()
    conn.close()
