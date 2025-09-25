import os, time, random, string
from datetime import datetime

DATA_DIR = os.getenv("DATA_DIR", "/data")
STATE_FILE = os.path.join(DATA_DIR, "state.txt")
INTERVAL = int(os.getenv("INTERVAL_SECONDS", "5"))

# Generate once on startup
random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
print(f"[writer] Generated string on startup: {random_str}", flush=True)

os.makedirs(DATA_DIR, exist_ok=True)

while True:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {random_str}\n"
    with open(STATE_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[writer] wrote: {line.strip()}", flush=True)
    time.sleep(INTERVAL)

