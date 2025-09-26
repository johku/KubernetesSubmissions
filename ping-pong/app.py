import os
from flask import Flask, Response

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
DATA_DIR = os.getenv("DATA_DIR", "/shared")
COUNTER_FILE = os.path.join(DATA_DIR, "pingpong-count.txt")

def read_count() -> int:
    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip() or "0")
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0

def write_count(n: int) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        f.write(str(n))

@app.get("/pingpong")
def pingpong():
    n = read_count()
    resp = f"pong {n}"
    write_count(n + 1)
    return Response(resp, mimetype="text/plain")

if __name__ == "__main__":
    print(f"Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

