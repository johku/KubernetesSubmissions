import os
from flask import Flask

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))
GREETING = os.getenv("GREETING", "Hello from todo-app in Kubernetes!")

# Required startup line
print(f"Server started in port {PORT}", flush=True)

@app.get("/")
def root():
    return f"""<!doctype html>
<html>
  <head><meta charset="utf-8"><title>todo-app</title></head>
  <body style="font-family: system-ui; padding: 1rem;">
    <h1>{GREETING}</h1>
    <p>Status: ok</p>
    <p>Listening on port <strong>{PORT}</strong>.</p>
  </body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

