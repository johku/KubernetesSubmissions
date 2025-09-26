import os
from datetime import datetime
from flask import Flask, Response

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
DATA_DIR = os.getenv("DATA_DIR", "/data")
STATE_FILE = os.path.join(DATA_DIR, "state.txt")             # written by writer
COUNTER_FILE = os.path.join(DATA_DIR, "pingpong-count.txt")  # written by ping-pong

def read_all(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

@app.get("/")
def root():
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>log_output</title></head>"
        "<body style='font-family:system-ui;padding:1rem'>"
        "<h1>log_output</h1>"
        "<p>See <a href='/status'>/status</a> for the combined output.</p>"
        "</body></html>"
    )

@app.get("/status")
def status():
    # last line from state file
    state = read_all(STATE_FILE) or ""
    last_line = state.strip().splitlines()[-1] if state.strip() else None

    # counter from ping-pong
    count_txt = read_all(COUNTER_FILE) or "0"
    try:
        count = int(count_txt.strip() or "0")
    except ValueError:
        count = 0

    # If writer hasn’t written yet, synthesize timestamp/random line
    if not last_line:
        now_iso = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        last_line = f"{now_iso}: (no-random-yet)."

    # Compose final 2-line output
    out = f"{last_line}\nPing / Pongs: {count}\n"
    return Response(out, mimetype="text/plain")

if __name__ == "__main__":
    print(f"[reader] Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

