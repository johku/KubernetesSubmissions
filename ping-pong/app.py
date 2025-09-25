import os
from flask import Flask, Response

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
counter = 0  # in-memory; resets on pod restart

@app.get("/pingpong")
def pingpong():
    global counter
    resp = f"pong {counter}"
    counter += 1
    # plain text response
    return Response(resp, mimetype="text/plain")

if __name__ == "__main__":
    print(f"Server started in port {PORT}", flush=True)
    app.run(host="0.0.0.0", port=PORT)

