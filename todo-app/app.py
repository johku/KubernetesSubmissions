import os
import time
import json
import requests
from flask import Flask, send_file, Response

app = Flask(__name__)

# ---- Config ----
PORT = int(os.getenv("PORT", "8080"))
DATA_DIR = os.getenv("DATA_DIR", "/data")            # persistent mount for image cache
TTL_SECONDS = int(os.getenv("IMAGE_TTL_SECONDS", "600"))  # default 10 minutes

IMG_PATH = os.path.join(DATA_DIR, "photo.jpg")
META_PATH = os.path.join(DATA_DIR, "photo_meta.json")

# ---- Image cache helpers ----
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
    # Get redirect to a random image and then download actual bytes
    r = requests.get("https://picsum.photos/1200", timeout=10)
    r.raise_for_status()
    img = requests.get(r.url, timeout=15)
    img.raise_for_status()
    with open(IMG_PATH, "wb") as f:
        f.write(img.content)
    _save_meta({"ts": time.time(), "grace_used": False})

# ---- Routes ----
@app.get("/")
def root():
    # Minimal SPA: image + todo form + list (calls backend at /api/todos)
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>todo-app</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
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
    .error {{ color: #c00; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>todo-app</h1>

    <img src="/image" alt="Random (cached) image" />
    <p class="muted">devops with kubernetes 2025</p>

    <h2 style="margin-top:18px;">Create a todo</h2>
    <div class="row">
      <input id="todoInput" type="text" maxlength="140"
             placeholder="What needs to be done? (max 140 chars)" />
      <button id="todoBtn" disabled>Create todo</button>
    </div>
    <div class="muted"><span id="counter">0</span>/140</div>
    <div id="error" class="error" style="display:none;"></div>

    <h2 style="margin-top:18px;">Existing todos</h2>
    <ul id="todoList"><li class="muted">Loading…</li></ul>
  </div>

  <script>
    const input = document.getElementById('todoInput');
    const btn = document.getElementById('todoBtn');
    const counter = document.getElementById('counter');
    const list = document.getElementById('todoList');
    const errorBox = document.getElementById('error');

    function setError(msg) {{
      if (!msg) {{ errorBox.style.display = 'none'; errorBox.textContent = ''; return; }}
      errorBox.textContent = msg;
      errorBox.style.display = 'block';
    }}

    function updateUI() {{
      const len = input.value.length;
      counter.textContent = len.toString();
      btn.disabled = !(len > 0 && len <= 140);
    }}
    input.addEventListener('input', updateUI);
    updateUI();

    async function loadTodos() {{
      try {{
        setError('');
        const r = await fetch('/api/todos', {{ cache: 'no-store' }});
        if (!r.ok) throw new Error('failed to fetch todos');
        const items = await r.json();
        list.innerHTML = items.length
          ? items.map(t => `<li>[#${{t.id}}] ${{t.text}}</li>`).join('')
          : '<li class="muted">No todos yet</li>';
      }} catch (e) {{
        list.innerHTML = '<li class="muted">Failed to load todos</li>';
        setError(e.message || 'failed to load todos');
      }}
    }}

    btn.addEventListener('click', async (e) => {{
      e.preventDefault();
      const text = input.value.trim();
      if (!text || text.length > 140) return;
      btn.disabled = true;
      try {{
        setError('');
        const r = await fetch('/api/todos', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ text }})
        }});
        if (!r.ok) {{
          const body = await r.json().catch(() => ({{}}));
          throw new Error(body.error || 'create failed');
        }}
        input.value = '';
        updateUI();
        await loadTodos();
      }} catch (e) {{
        setError(e.message || 'failed to create todo');
      }} finally {{
        btn.disabled = false;
      }}
    }});

    loadTodos();
  </script>
</body>
</html>"""
    return Response(html, mimetype="text/html")

@app.get("/image")
def image():
    need_new, _ = _need_new_image()
    if need_new or not os.path.exists(IMG_PATH):
        try:
            _fetch_and_store()
        except Exception as e:
            # Degrade gracefully if Picsum is unavailable
            return Response(f"Image fetch failed: {e}\n", status=503, mimetype="text/plain")
    return send_file(IMG_PATH, mimetype="image/jpeg")

@app.get("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    print(f"Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

