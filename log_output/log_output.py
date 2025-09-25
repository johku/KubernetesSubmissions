import os, time, random, string
from datetime import datetime
from threading import Thread, Event
from flask import Flask, jsonify

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))

# state kept in memory
random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
last_ts = None
stop_event = Event()

def ticker():
    global last_ts
    print(f"Generated string on startup: {random_str}", flush=True)
    while not stop_event.is_set():
        last_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{last_ts}] Stored string: {random_str}", flush=True)
        time.sleep(5)

@app.get("/status")
def status():
    return jsonify(timestamp=last_ts, random_string=random_str)

@app.get("/")
def root():
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>log_output</title></head>"
        "<body style='font-family:system-ui;padding:1rem'>"
        "<h1>log_output</h1>"
        "<p>Try <a href=\"/status\">/status</a> for JSON.</p>"
        "</body></html>"
    )

if __name__ == "__main__":
    # background logging thread
    Thread(target=ticker, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)

