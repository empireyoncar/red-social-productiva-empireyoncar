from flask import Flask, request, jsonify
from flask_cors import CORS
from db_grupos import get_db, init_db

app = Flask(__name__)
CORS(app)

init_db()


@app.post("/api/grupos/crear")
def crear_grupo():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400
    nombre = data.get("nombre")
    descripcion = data.get("descripcion")
    imagen = data.get("imagen")
    admin_id = data.get("admin_id")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO grupos (nombre, descripcion, imagen, admin_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, (nombre, descripcion, imagen, admin_id))
    grupo_id = cur.fetchone()["id"]
    cur.execute("""
        INSERT INTO miembros_grupo (grupo_id, user_id, rol)
        VALUES (%s, %s, 'admin')
        ON CONFLICT DO NOTHING;
    """, (grupo_id, admin_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok", "grupo_id": grupo_id})


@app.get("/api/grupos/lista")
def lista_grupos():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM grupos ORDER BY fecha DESC;")
    grupos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(grupos)


@app.post("/api/grupos/solicitar")
def solicitar_unirse():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400
    grupo_id = data.get("grupo_id")
    user_id = data.get("user_id")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM miembros_grupo WHERE grupo_id = %s AND user_id = %s;", (grupo_id, user_id))
    if cur.fetchone():
        return jsonify({"error": "Ya eres miembro"}), 400
    cur.execute("SELECT 1 FROM solicitudes_grupo WHERE grupo_id = %s AND user_id = %s AND estado = 'pendiente';", (grupo_id, user_id))
    if cur.fetchone():
        return jsonify({"error": "Solicitud ya enviada"}), 400
    cur.execute("""
        INSERT INTO solicitudes_grupo (grupo_id, user_id)
        VALUES (%s, %s)
        RETURNING id;
    """, (grupo_id, user_id))
    solicitud_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok", "solicitud_id": solicitud_id})


@app.get("/api/grupos/solicitudes/<int:grupo_id>")
def solicitudes_pendientes(grupo_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM solicitudes_grupo WHERE grupo_id = %s AND estado = 'pendiente' ORDER BY fecha ASC;", (grupo_id,))
    solicitudes = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(solicitudes)


@app.post("/api/grupos/solicitud/accion")
def accion_solicitud():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido o vacío"}), 400
    solicitud_id = data.get("solicitud_id")
    accion = data.get("accion")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM solicitudes_grupo WHERE id = %s;", (solicitud_id,))
    solicitud = cur.fetchone()
    if not solicitud:
        return jsonify({"error": "Solicitud no existe"}), 404
    cur.execute("UPDATE solicitudes_grupo SET estado = %s WHERE id = %s;", (accion, solicitud_id))
    if accion == "aprobar":
        cur.execute("""
            INSERT INTO miembros_grupo (grupo_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (solicitud["grupo_id"], solicitud["user_id"]))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": accion})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5107, debug=True)
