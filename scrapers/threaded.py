import csv, json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import requests
from bs4 import BeautifulSoup
from common import UA, ROOT, allowed, log_request
from bs4_scraper import WANTED, LEAGUE_ID, SEASON_ID, SLUG, URL as PAGE_URL

API_URL = "https://data.fotmob.com/stats/{lg}/season/{se}/{stat}.json"
_local = threading.local()
_log_lock = threading.Lock()


class RateLimiter:
    """One shared speed limit: a new request may start only every `interval` seconds, whatever the number of threads."""
    def __init__(self, interval):
        self.interval, self.lock, self.next = interval, threading.Lock(), 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            start = max(now, self.next)
            self.next = start + self.interval
        if start > now:
            time.sleep(start - now)


def session():
    if not hasattr(_local, "s"):          # one connection per thread (a Session is not guaranteed thread-safe)
        _local.s = requests.Session()
    return _local.s


def url_for(method, stat):
    template = API_URL if method == "api" else PAGE_URL
    return template.format(lg=LEAGUE_ID, se=SEASON_ID, stat=stat, slug=SLUG)


def count_players(method, r):
    if method == "api":
        return len(r.json()["TopLists"][0]["StatList"])
    soup = BeautifulSoup(r.text, "lxml")
    data = json.loads(soup.find("script", id="__NEXT_DATA__").string)
    return len(data["props"]["pageProps"]["data"]["statsData"])


def fetch(args):
    method, stat, limiter = args
    url, error, sent = url_for(method, stat), None, 0
    for attempt in (1, 2):                 # one retry if a request fails
        limiter.wait()
        sent += 1
        t0 = time.time()
        try:
            r = session().get(url, headers={"User-Agent": UA}, timeout=(5, 20))
            dt = time.time() - t0
            with _log_lock:
                log_request(method + "_mt", url, r.status_code, len(r.content), dt)
            if r.status_code != 200:
                error = f"HTTP {r.status_code}"
                continue
            return {"stat": stat, "ok": True, "bytes": len(r.content), "seconds": dt,
                    "players": count_players(method, r), "sent": sent}
        except Exception as e:
            error = type(e).__name__
    return {"stat": stat, "ok": False, "bytes": 0, "seconds": 0.0, "players": None, "sent": sent, "error": error}


def run(method, workers, interval):
    allowed(url_for(method, WANTED[0]))    # robots.txt is read once, before the threads start
    limiter = RateLimiter(interval)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(fetch, [(method, s, limiter) for s in WANTED]))
    total = time.time() - t0
    ok = [r for r in res if r["ok"]]
    sent = sum(r["sent"] for r in res)

    match = "n/a"
    csv_path = os.path.join(ROOT, "data", f"{method}_data.csv")
    if os.path.exists(csv_path):           # same data as the normal scraper's CSV?
        counts = pd.read_csv(csv_path).notna().sum()
        good = sum(1 for r in ok if r["stat"] in counts and counts[r["stat"]] == r["players"])
        match = f"{good}/{len(WANTED)}"

    row = {"method": method, "workers": workers, "interval_s": interval, "total_s": round(total, 1),
           "requests_sent": sent, "failed": len(res) - len(ok),
           "avg_latency_ms": round(sum(r["seconds"] for r in ok) / max(len(ok), 1) * 1000),
           "requests_per_s": round(sent / total, 2), "body_KB": round(sum(r["bytes"] for r in ok) / 1024),
           "same_data_as_csv": match}
    print(row)
    path = os.path.join(ROOT, "network", "threading_results.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("api", "bs4"):
        sys.exit("usage: python scrapers/threaded.py <api|bs4> <workers> <interval_seconds>")
    run(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]))
