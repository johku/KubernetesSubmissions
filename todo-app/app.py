import os, time, json, requests
from flask import Flask, send_file, Response

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
DATA_DIR = os.getenv("DATA_DIR", "/data")  # Persistent volume mount
TTL_SECONDS = int(os.getenv("IMAGE_TTL_SECONDS", "600"))  # default 10 min

IMG_PATH = os.path.join(DATA_DIR, "photo.jpg")
META_PATH = os.path.join(DATA_DIR, "photo_meta.json")

def _load_meta():
    try:
        with open(META_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"ts": 0, "grace_used": False}
    except json.JSONDecodeError:
        return {"ts": 0, "grace_used": False}

def _save_meta(meta):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f)

def _need_new_image():
    meta = _load_meta()
    age = time.time() - meta.get("ts", 0)
    # Fresh within TTL -> keep
    if age < TTL_SECONDS:
        return False, meta
    # Expired but grace not used -> serve once more, mark grace
    if not meta.get("grace_used", False):
        meta["grace_used"] = True
        _save_meta(meta)
        return False, meta
    # Expired and grace used -> fetch a new one
    return True, meta

def _fetch_and_store():
    os.makedirs(DATA_DIR, exist_ok=True)
    # Get a random 1200px image (redirects to a random JPEG)
    r = requests.get("https://picsum.photos/1200", timeout=10)
    r.raise_for_status()
    # Follow final image location to store real bytes
    img = requests.get(r.url, timeout=15)
    img.raise_for_status()
    with open(IMG_PATH, "wb") as f:
        f.write(img.content)
    meta = {"ts": time.time(), "grace_used": False}
    _save_meta(meta)

@app.get("/")
def root():
    # Simple page with title, image, and footer
    return Response(
        "<!doctype html>"
        "<html><head><meta charset='utf-8'><title>todo-app</title>"
        "<style>body{font-family:system-ui;margin:24px;max-width:1200px}"
        "h1{margin-bottom:8px}img{max-width:100%;height:auto;border-radius:8px}</style>"
        "</head><body>"
        "<h1>todo-app</h1>"
        "<img src='/image' alt='Random (cached) image'/>"
        "<p>devops with kubernetes 2025</p>"
        "</body></html>",
        mimetype="text/html",
    )

@app.get("/image")
def image():
    need_new, _ = _need_new_image()
    if need_new or not os.path.exists(IMG_PATH):
        try:
            _fetch_and_store()
        except Exception as e:
            # Fallback: if we cannot download, show a tiny inline placeholder
            return Response(f"Image fetch failed: {e}\n", status=503, mimetype="text/plain")
    # Always serve the same file path; browser cache is fine
    return send_file(IMG_PATH, mimetype="image/jpeg")

if __name__ == "__main__":
    print(f"Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

