# app.py
import time, random, string
from datetime import datetime

def generate_random_string(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

random_str = generate_random_string()
print(f"Generated string on startup: {random_str}", flush=True)

while True:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Stored string: {random_str}", flush=True)
    time.sleep(5)
