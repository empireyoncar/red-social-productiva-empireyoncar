import psycopg2
from psycopg2.extras import RealDictCursor

from db_bootstrap import ensure_database

DB_CONFIG = {
    "host": "postgres",
    "database": "posts_db",
    "user": "admin",
    "password": "admin123",
    "port": 5151,
}

ensure_database(DB_CONFIG["database"])


def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


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

    cur.execute("ALTER TABLE posts ALTER COLUMN contenido SET DEFAULT '';")
    cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS link_url TEXT;")
    cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS link_title TEXT;")
    cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS link_description TEXT;")
    cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS link_image TEXT;")
    cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS poll_question TEXT;")
    cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS poll_options JSONB;")
    cur.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS poll_votes JSONB;")

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


def create_post_record(payload, json_adapter):
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
        payload["user_id"],
        payload["contenido"],
        payload["imagen"],
        payload["link_url"],
        payload["link_title"],
        payload["link_description"],
        payload["link_image"],
        payload["poll_question"],
        json_adapter(payload["poll_options"]) if payload["poll_options"] else None,
        json_adapter(payload["poll_votes"]) if payload["poll_votes"] else None,
    ))

    post = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return post


def list_posts_by_user(user_id):
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
    return posts


def list_feed_posts():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.*
        FROM posts p
        ORDER BY p.fecha DESC
        LIMIT 50;
    """)

    posts = cur.fetchall()
    cur.close()
    conn.close()
    return posts


def get_poll_for_post(post_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT poll_options, poll_votes FROM posts WHERE id = %s", (post_id,))
    post = cur.fetchone()
    cur.close()
    conn.close()
    return post


def register_poll_vote(post_id, user_id, option_index, votes, json_adapter):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO poll_responses (post_id, user_id, option_index)
            VALUES (%s, %s, %s)
        """, (post_id, user_id, option_index))
        cur.execute(
            "UPDATE posts SET poll_votes = %s WHERE id = %s",
            (json_adapter(votes), post_id),
        )
        conn.commit()
    except psycopg2.Error:
        conn.rollback()
        cur.close()
        conn.close()
        raise

    cur.close()
    conn.close()


def register_like(user_id, post_id):
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
        raise

    cur.close()
    conn.close()


def create_comment(post_id, user_id, comentario):
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
    return comentario_db


def list_comments(post_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*
        FROM comentarios c
        WHERE post_id = %s
        ORDER BY fecha ASC;
    """, (post_id,))
    comentarios = cur.fetchall()
    cur.close()
    conn.close()
    return comentarios


def get_post_owner(post_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
    post = cur.fetchone()
    cur.close()
    conn.close()
    return post


def delete_post_record(post_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))
    conn.commit()
    cur.close()
    conn.close()
