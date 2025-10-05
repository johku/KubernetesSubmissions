import os
import threading
from flask import Flask, Response

app = Flask(__name__)

# Configuration via env (no hard-coded values)
PORT = int(os.getenv("PORT", "8080"))
COUNTER_FILE = os.getenv("COUNTER_FILE")          # e.g., "/data/counter.txt" (optional)

_lock = threading.Lock()
_counter = 0

def _load_counter():
    """Load counter from file if COUNTER_FILE is set; otherwise start at 0."""
    if not COUNTER_FILE:
        return 0
    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip() or "0")
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0

def _save_counter(value: int):
    """Persist counter if COUNTER_FILE is set."""
    if not COUNTER_FILE:
        return
    # Ensure directory exists
    os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)
    # Write atomically
    tmp = COUNTER_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(str(value))
    os.replace(tmp, COUNTER_FILE)

# Initialize from disk if configured
_counter = _load_counter()

@app.get("/pingpong")
def pingpong():
    global _counter
    with _lock:
        n = _counter
        _counter += 1
        _save_counter(_counter)
    return Response(f"pong {n}", mimetype="text/plain")

@app.get("/pings")
def pings():
    with _lock:
        value = _counter
    return Response(str(value), mimetype="text/plain")

@app.get("/healthz")
def healthz():
    return Response("ok", mimetype="text/plain")

if __name__ == "__main__":
    print(f"[ping-pong] PORT={PORT}", flush=True)
    if COUNTER_FILE:
        print(f"[ping-pong] COUNTER_FILE={COUNTER_FILE}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

