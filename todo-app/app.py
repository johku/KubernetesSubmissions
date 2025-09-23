import os
from flask import Flask, jsonify

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))

# Print the required startup line
print(f"Server started in port {PORT}", flush=True)

@app.get("/")
def root():
    return jsonify(status="ok", app="todo-app", note="API to be expanded soon")

if __name__ == "__main__":
    # Bind to 0.0.0.0 so Kubernetes can reach it inside the Pod
    app.run(host="0.0.0.0", port=PORT)
