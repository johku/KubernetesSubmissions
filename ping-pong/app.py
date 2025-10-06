import os, time
import psycopg2
from flask import Flask, Response

app = Flask(__name__)

# App config (env-driven)
PORT = int(os.getenv("PORT", "8080"))

# DB config (env-driven via ConfigMap/Secret)
PGHOST = os.getenv("PGHOST", "postgres")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "pingpong")
PGUSER = os.getenv("PGUSER", "pingpong")
PGPASSWORD = os.getenv("PGPASSWORD", "changeme")
DB_CONNECT_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "20"))
DB_CONNECT_BACKOFF = float(os.getenv("DB_CONNECT_BACKOFF", "0.5"))

def dsn():
    return f"dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD} host={PGHOST} port={PGPORT}"

def _connect_with_retry():
    last_err = None
    for i in range(DB_CONNECT_RETRIES):
        try:
            conn = psycopg2.connect(dsn())
            conn.autocommit = True
            return conn
        except Exception as e:
            last_err = e
            time.sleep(DB_CONNECT_BACKOFF * (i + 1))
    raise last_err

# Global connection (simple for demo)
_conn = _connect_with_retry()

def _ensure_schema():
    with _conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ping_counter (
                id INT PRIMARY KEY,
                value INT NOT NULL
            );
        """)
        cur.execute("INSERT INTO ping_counter(id, value) VALUES (1, 0) ON CONFLICT (id) DO NOTHING;")

_ensure_schema()

@app.get("/pingpong")
def pingpong():
    with _conn.cursor() as cur:
        # increment and return previous value, atomically
        cur.execute("""
            UPDATE ping_counter
               SET value = value + 1
             WHERE id = 1
         RETURNING value - 1;
        """)
        (previous,) = cur.fetchone()
    return Response(f"pong {previous}", mimetype="text/plain")

@app.get("/pings")
def pings():
    with _conn.cursor() as cur:
        cur.execute("SELECT value FROM ping_counter WHERE id = 1;")
        row = cur.fetchone()
        count = row[0] if row else 0
    return Response(str(count), mimetype="text/plain")

@app.get("/healthz")
def healthz():
    try:
        with _conn.cursor() as cur:
            cur.execute("SELECT 1;")
        return "ok", 200
    except Exception as e:
        return f"db error: {e}", 500

if __name__ == "__main__":
    print(f"[ping-pong] PORT={PORT}", flush=True)
    print(f"[ping-pong] DB={PGUSER}@{PGHOST}:{PGPORT}/{PGDATABASE}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

