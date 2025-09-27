import os
from flask import Flask, Response

app = Flask(__name__)
PORT = int(os.getenv("PORT", "8080"))

_counter = 0

@app.get("/pingpong")
def pingpong():
    global _counter
    n = _counter
    _counter += 1
    return Response(f"pong {n}", mimetype="text/plain")

@app.get("/pings")
def pings():
    return Response(str(_counter), mimetype="text/plain")

if __name__ == "__main__":
    print(f"Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

