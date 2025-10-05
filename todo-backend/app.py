import os, time, threading
from flask import Flask, Blueprint, request, jsonify

# ---- Configuration via env (no hard-coded constants) ----
PORT = int(os.getenv("PORT", "8080"))
API_PREFIX = os.getenv("API_PREFIX", "/api")          # e.g., "/api"
MAX_TODO_LENGTH = int(os.getenv("MAX_TODO_LENGTH", "140"))

app = Flask(__name__)

# Optional: limit request size (bytes), configurable as well
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "0"))  # 0 = disabled
if MAX_CONTENT_LENGTH > 0:
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# In-memory store
todos, _next_id = [], 1
_lock = threading.Lock()

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# ---- API Blueprint so the path prefix is configurable ----
api = Blueprint("api", __name__)

@api.get("/todos")
def get_todos():
    with _lock:
        return jsonify(list(todos))

@api.post("/todos")
def create_todo():
    global _next_id
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify(error="text is required"), 400
    if len(text) > MAX_TODO_LENGTH:
        return jsonify(error=f"text must be <= {MAX_TODO_LENGTH} chars"), 400

    with _lock:
        item = {"id": _next_id, "text": text, "createdAt": now_iso()}
        _next_id += 1
        todos.append(item)
    return jsonify(item), 201

# Health endpoint (not under API prefix on purpose)
@app.get("/healthz")
def healthz():
    return "ok", 200

# Register API with configurable prefix
app.register_blueprint(api, url_prefix=API_PREFIX)

if __name__ == "__main__":
    print(f"[todo-backend] PORT={PORT}", flush=True)
    print(f"[todo-backend] API_PREFIX={API_PREFIX}", flush=True)
    print(f"[todo-backend] MAX_TODO_LENGTH={MAX_TODO_LENGTH}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

