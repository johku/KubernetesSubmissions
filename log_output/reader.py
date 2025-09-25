import os
from flask import Flask, Response

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
DATA_DIR = os.getenv("DATA_DIR", "/data")
STATE_FILE = os.path.join(DATA_DIR, "state.txt")

@app.get("/")
def root():
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>log_output</title></head>"
        "<body style='font-family:system-ui;padding:1rem'>"
        "<h1>log_output (sidecar)</h1>"
        "<p>See <a href='/status'>/status</a> for the file contents.</p>"
        "</body></html>"
    )

@app.get("/status")
def status():
    if not os.path.exists(STATE_FILE):
        return Response("No data yet.\n", mimetype="text/plain")
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    # plain text for easy viewing
    return Response(content if content else "No data yet.\n", mimetype="text/plain")

if __name__ == "__main__":
    print(f"[reader] Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

