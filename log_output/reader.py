import os, requests
from datetime import datetime
from flask import Flask, Response

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
DATA_DIR = os.getenv("DATA_DIR", "/data")        # in-pod only
STATE_FILE = os.path.join(DATA_DIR, "state.txt")
PINGPONG_URL = os.getenv("PINGPONG_URL", "http://ping-pong-svc/pings")

def read_last_line(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
            return lines[-1] if lines else None
    except FileNotFoundError:
        return None

@app.get("/status")
def status():
    last = read_last_line(STATE_FILE)
    if not last:
        now = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        last = f"{now}: (no-random-yet)."

    count = 0
    try:
        r = requests.get(PINGPONG_URL, timeout=1.5)
        r.raise_for_status()
        count = int(r.text.strip())
    except Exception:
        count = 0

    return Response(f"{last}\nPing / Pongs: {count}\n", mimetype="text/plain")

if __name__ == "__main__":
    print(f"[reader] Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

