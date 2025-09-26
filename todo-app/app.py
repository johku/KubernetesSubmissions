import os, time, json, requests
from flask import Flask, send_file, Response

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
DATA_DIR = os.getenv("DATA_DIR", "/data")
TTL_SECONDS = int(os.getenv("IMAGE_TTL_SECONDS", "600"))  # 10 minutes

IMG_PATH = os.path.join(DATA_DIR, "photo.jpg")
META_PATH = os.path.join(DATA_DIR, "photo_meta.json")

# --- Image cache helpers (unchanged idea) ---
def _load_meta():
    try:
        with open(META_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"ts": 0, "grace_used": False}

def _save_meta(meta):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f)

def _need_new_image():
    meta = _load_meta()
    age = time.time() - meta.get("ts", 0)
    if age < TTL_SECONDS:
        return False, meta
    if not meta.get("grace_used", False):
        meta["grace_used"] = True
        _save_meta(meta)
        return False, meta
    return True, meta

def _fetch_and_store():
    os.makedirs(DATA_DIR, exist_ok=True)
    r = requests.get("https://picsum.photos/1200", timeout=10)
    r.raise_for_status()
    img = requests.get(r.url, timeout=15)
    img.raise_for_status()
    with open(IMG_PATH, "wb") as f:
        f.write(img.content)
    _save_meta({"ts": time.time(), "grace_used": False})

# --- Simple, hardcoded todos for now ---
HARDCODED_TODOS = [
    "learn k8s Deployments",
    "hook Services + Ingress",
    "persist images with PVC",
]

@app.get("/")
def root():
    # Minimal inline UI: title, image, input (max 140), button, hardcoded list
    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>todo-app</title>
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; }}
    .wrap {{ max-width: 900px; margin: 0 auto; }}
    img {{ max-width: 100%; height: auto; border-radius: 10px; }}
    .row {{ display: flex; gap: 8px; margin: 12px 0; }}
    input[type=text] {{ flex: 1; padding: 10px; border-radius: 8px; border: 1px solid #aaa; }}
    button {{ padding: 10px 14px; border-radius: 8px; border: 1px solid #888; cursor: pointer; }}
    .muted {{ color: #888; font-size: 0.9rem; }}
    ul {{ padding-left: 1.2rem; }}
    li {{ margin: 6px 0; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>todo-app</h1>
    <img src="/image" alt="Random (cached) image" />

    <h2 style="margin-top:18px;">Create a todo</h2>
    <div class="row">
      <input id="todoInput" type="text" maxlength="140" placeholder="What needs to be done? (max 140 chars)" />
      <button id="todoBtn" disabled>Create todo</button>
    </div>
    <div class="muted">
      <span id="counter">0</span>/140
      &middot;
      (button is a no-op for this step)
    </div>

    <h2 style="margin-top:18px;">Existing todos</h2>
    <ul id="todoList">
      {"".join(f"<li>{t}</li>" for t in HARDCODED_TODOS)}
    </ul>

    <p class="muted">devops with kubernetes 2025</p>
  </div>

  <script>
    const input = document.getElementById('todoInput');
    const btn   = document.getElementById('todoBtn');
    const counter = document.getElementById('counter');

    function updateUI() {{
      const len = input.value.length;
      counter.textContent = len.toString();
      // enable if 1..140
      btn.disabled = !(len > 0 && len <= 140);
    }}
    input.addEventListener('input', updateUI);
    updateUI();

    // For this exercise, clicking doesn't submit yet.
    btn.addEventListener('click', (e) => {{
      e.preventDefault();
      // no-op now; next exercise we’ll wire backend
      alert('Submit not implemented yet (will be in next step).');
    }});
  </script>
</body>
</html>
"""
    return Response(html, mimetype="text/html")

@app.get("/image")
def image():
    need_new, _ = _need_new_image()
    if need_new or not os.path.exists(IMG_PATH):
        try:
            _fetch_and_store()
        except Exception as e:
            return Response(f"Image fetch failed: {e}\\n", status=503, mimetype="text/plain")
    return send_file(IMG_PATH, mimetype="image/jpeg")

if __name__ == "__main__":
    print(f"Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

