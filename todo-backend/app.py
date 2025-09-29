import os, time
from flask import Flask, request, jsonify
app = Flask(__name__)
PORT = int(os.getenv("PORT", "8080"))
todos, _next_id = [], 1
def now_iso(): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

@app.get("/api/todos")
def get_todos():
    return jsonify(todos)

@app.post("/api/todos")
def create_todo():
    global _next_id
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text: return jsonify(error="text is required"), 400
    if len(text) > 140: return jsonify(error="text must be <= 140 chars"), 400
    item = {"id": _next_id, "text": text, "createdAt": now_iso()}
    _next_id += 1
    todos.append(item)
    return jsonify(item), 201

@app.get("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    print(f"todo-backend: listening on {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

