import os, time, threading
import psycopg2
from flask import Flask, Blueprint, request, jsonify

# ---- Config (env-driven) ----
PORT = int(os.getenv("PORT", "8080"))
API_PREFIX = os.getenv("API_PREFIX", "/api")
MAX_TODO_LENGTH = int(os.getenv("MAX_TODO_LENGTH", "140"))

PGHOST = os.getenv("PGHOST", "todo-postgres")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "todos")
PGUSER = os.getenv("PGUSER", "todoapp")
PGPASSWORD = os.getenv("PGPASSWORD", "changeme")
DB_CONNECT_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "30"))
DB_CONNECT_BACKOFF = float(os.getenv("DB_CONNECT_BACKOFF", "0.5"))

def dsn():
    return f"dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD} host={PGHOST} port={PGPORT}"

def connect_with_retry():
    last = None
    for i in range(DB_CONNECT_RETRIES):
        try:
            conn = psycopg2.connect(dsn())
            conn.autocommit = True
            return conn
        except Exception as e:
            last = e
            time.sleep(DB_CONNECT_BACKOFF * (i + 1))
    raise last

app = Flask(__name__)
api = Blueprint("api", __name__)

_conn = connect_with_retry()

def ensure_schema():
    with _conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id SERIAL PRIMARY KEY,
                text VARCHAR(512) NOT NULL,
                "createdAt" TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

ensure_schema()
_lock = threading.Lock()

@api.get("/todos")
def get_todos():
    with _conn.cursor() as cur:
        cur.execute('SELECT id, text, "createdAt" FROM todos ORDER BY id ASC;')
        rows = cur.fetchall()
    items = [{"id": r[0], "text": r[1], "createdAt": r[2].strftime("%Y-%m-%dT%H:%M:%SZ")} for r in rows]
    return jsonify(items)

@api.post("/todos")
def create_todo():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify(error="text is required"), 400
    if len(text) > MAX_TODO_LENGTH:
        return jsonify(error=f"text must be <= {MAX_TODO_LENGTH} chars"), 400
    with _conn.cursor() as cur:
        cur.execute('INSERT INTO todos(text) VALUES (%s) RETURNING id, "createdAt";', (text,))
        row = cur.fetchone()
    item = {"id": row[0], "text": text, "createdAt": row[1].strftime("%Y-%m-%dT%H:%M:%SZ")}
    return jsonify(item), 201

@app.get("/healthz")
def healthz():
    try:
        with _conn.cursor() as cur:
            cur.execute("SELECT 1;")
        return "ok", 200
    except Exception as e:
        return f"db error: {e}", 500

app.register_blueprint(api, url_prefix=API_PREFIX)

if __name__ == "__main__":
    print(f"[todo-backend] PORT={PORT}", flush=True)
    print(f"[todo-backend] DB={PGUSER}@{PGHOST}:{PGPORT}/{PGDATABASE}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

