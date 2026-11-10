import csv, os, sys, time
import requests
from common import UA, ROOT

label = sys.argv[1] if len(sys.argv) > 1 else "test"
PAGE = "https://www.fotmob.com/leagues/87/stats/season/38843/players/goals/laliga"
JSON = "https://data.fotmob.com/stats/87/season/38843/goals.json"

def http(url):
    t0 = time.time()
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=10)
        return f"HTTP {r.status_code}", time.time() - t0
    except Exception as e:
        return type(e).__name__, time.time() - t0

def browser(url):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    o = Options()
    for a in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage"):
        o.add_argument(a)
    d = webdriver.Chrome(options=o)
    d.set_page_load_timeout(20)
    t0 = time.time()
    try:
        d.get(url)
        return f"loaded, title: {d.title[:30]}", time.time() - t0
    except Exception as e:
        msg = str(e).split("\n")[0]
        return f"{type(e).__name__}: {msg[:60]}", time.time() - t0
    finally:
        d.quit()

rows = []
for name, fn, url in [("API (JSON file)", http, JSON), ("BS4 (HTML page)", http, PAGE), ("Selenium (browser)", browser, PAGE)]:
    outcome, secs = fn(url)
    print(f"{name:20s} -> {outcome} ({secs:.1f} s)")
    rows.append([label, name, outcome, round(secs, 1)])

path = os.path.join(ROOT, "network", "firewall_results.csv")
os.makedirs(os.path.dirname(path), exist_ok=True)
new = not os.path.exists(path)
with open(path, "a", newline="") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["condition", "method", "outcome", "seconds"])
    w.writerows(rows)
