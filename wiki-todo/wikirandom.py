import os, requests, time

BACKEND_URL = os.getenv("BACKEND_URL", "http://todo-backend-svc/api/todos")

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def get_random_article():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; wiki-todo/1.0; +https://en.wikipedia.org/)"}
    try:
        r = requests.get(
            "https://en.wikipedia.org/wiki/Special:Random",
            allow_redirects=False,
            headers=headers,
            timeout=5,
        )
        if r.status_code in (301, 302, 303, 307, 308):
            return r.headers.get("Location", "https://en.wikipedia.org/wiki/Main_Page")
        return "https://en.wikipedia.org/wiki/Main_Page"
    except Exception as e:
        print(f"❌ Failed to fetch random article: {e}", flush=True)
        return "https://en.wikipedia.org/wiki/Main_Page"

def main():
    article_url = get_random_article()
    todo_text = f"Read {article_url}"
    payload = {"text": todo_text}
    print(f"Creating todo: {todo_text}", flush=True)
    try:
        r = requests.post(BACKEND_URL, json=payload, timeout=5)
        r.raise_for_status()
        print("✅ Created:", r.json(), flush=True)
    except Exception as e:
        print(f"❌ Failed to create todo: {e}", flush=True)

if __name__ == "__main__":
    main()

