import os, sys, time, threading, json, logging
import psycopg2
from flask import Flask, Blueprint, request, jsonify

# ---------- Config (env-driven) ----------
PORT = int(os.getenv("PORT", "8080"))
API_PREFIX = os.getenv("API_PREFIX", "/api")
MAX_TODO_LENGTH = int(os.getenv("MAX_TODO_LENGTH", "140"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

PGHOST = os.getenv("PGHOST", "todo-postgres")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "todos")
PGUSER = os.getenv("PGUSER", "todoapp")
PGPASSWORD = os.getenv("PGPASSWORD", "changeme")
DB_CONNECT_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "30"))
DB_CONNECT_BACKOFF = float(os.getenv("DB_CONNECT_BACKOFF", "0.5"))

# ---------- Logging to stdout (picked up by Promtail) ----------
logging.basicConfig(
    level=LOG_LEVEL,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("todo-backend")

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

# ---------- Request / Response logging ----------
def _remote_ip():
    # When behind Traefik, X-Forwarded-For is set
    xff = request.headers.get("X-Forwarded-For")
    return (xff.split(",")[0].strip() if xff else request.remote_addr) or "-"

def _body_preview():
    try:
        obj = request.get_json(silent=True)
    except Exception:
        obj = None
    # Limit preview size for logs
    txt = json.dumps(obj) if obj is not None else ""
    return txt[:200]  # cap preview

@app.before_request
def _log_request():
    if request.path.startswith("/healthz"):
        return
    log.info(
        "REQ method=%s path=%s ip=%s body=%s",
        request.method, request.path, _remote_ip(), _body_preview()
    )

@app.after_request
def _log_response(resp):
    if request.path.startswith("/healthz"):
        return resp
    log.info(
        "RESP method=%s path=%s status=%s",
        request.method, request.path, resp.status
    )
    return resp

# ---------- API ----------
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
        log.warning("Rejected todo: empty text ip=%s", _remote_ip())
        return jsonify(error="text is required"), 400

    if len(text) > MAX_TODO_LENGTH:
        log.warning(
            "Rejected todo: too_long length=%s limit=%s preview=%s ip=%s",
            len(text), MAX_TODO_LENGTH, text[:80], _remote_ip()
        )
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
    log.info("[startup] PORT=%s API_PREFIX=%s MAX_TODO_LENGTH=%s", PORT, API_PREFIX, MAX_TODO_LENGTH)
    log.info("[startup] DB=%s@%s:%s/%s", PGUSER, PGHOST, PGPORT, PGDATABASE)
    app.run(host="0.0.0.0", port=PORT)

