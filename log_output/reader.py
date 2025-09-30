import os
import requests
from datetime import datetime
from flask import Flask, Response

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
DATA_DIR = os.getenv("DATA_DIR", "/data")        # in-pod only
STATE_FILE = os.path.join(DATA_DIR, "state.txt")
PINGPONG_URL = os.getenv("PINGPONG_URL", "http://ping-pong-svc/pings")

# ConfigMap mounts
CONFIG_FILE_PATH = "/etc/config/information.txt"  # provided by the ConfigMap volume
MESSAGE = os.getenv("MESSAGE", "(no message)")

def read_last_line(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
            return lines[-1] if lines else None
    except FileNotFoundError:
        return None

def read_config_file():
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "(file missing)"

@app.get("/status")
def status():
    # 1) ConfigMap data
    file_content = read_config_file()
    message = os.getenv("MESSAGE", MESSAGE)

    # 2) Usual state line
    last = read_last_line(STATE_FILE)
    if not last:
        now = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        last = f"{now}: (no-random-yet)."

    # 3) Ping-pong count via HTTP
    count = 0
    try:
        r = requests.get(PINGPONG_URL, timeout=1.5)
        r.raise_for_status()
        count = int(r.text.strip())
    except Exception:
        count = 0

    body = (
        f"file content: {file_content}\n"
        f"env variable: MESSAGE={message}\n"
        f"{last}\n"
        f"Ping / Pongs: {count}\n"
    )
    return Response(body, mimetype="text/plain")

if __name__ == "__main__":
    # Print config on startup too (handy in logs)
    print(f"[reader] MESSAGE={MESSAGE}", flush=True)
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            print(f"[reader] information.txt: {f.read().strip()}", flush=True)
    except FileNotFoundError:
        print("[reader] information.txt: (file missing)", flush=True)

    print(f"[reader] Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

