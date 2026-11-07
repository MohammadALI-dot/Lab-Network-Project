import csv, os, time
from datetime import datetime
from urllib import robotparser
from urllib.parse import urlparse
import requests

UA = "Mozilla/5.0 (student project - university networking lab)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(ROOT, "network", "request_log.csv")
_robots = {}

def allowed(url):
    """Return True if the site's robots.txt allows us to fetch this URL."""
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = robotparser.RobotFileParser()
        rp.set_url(base + "/robots.txt")
        try:
            rp.read()
        except Exception:
            pass
        _robots[base] = rp
    return _robots[base].can_fetch(UA, url)

def log_request(method, url, status, nbytes, seconds):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    new = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "method", "url", "status", "bytes", "seconds"])
        w.writerow([datetime.now().isoformat(timespec="seconds"),
                    method, url, status, nbytes, round(seconds, 3)])

def polite_get(session, url, method, delay=2.0):
    """GET a URL if robots.txt allows it, wait `delay` seconds, and log it."""
    if not allowed(url):
        print("Blocked by robots.txt:", url)
        return None
    start = time.time()
    r = session.get(url, headers={"User-Agent": UA}, timeout=30)
    elapsed = time.time() - start
    log_request(method, url, r.status_code, len(r.content), elapsed)
    time.sleep(delay)
    return r
