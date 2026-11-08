import os, re, sys, time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common import allowed, log_request, UA, ROOT
from bs4_scraper import WANTED, LEAGUE_ID, SEASON_ID, SLUG, URL

ROWS = "a[aria-label^='#']"
FILTERS = ["Striker", "Winger", "Attacking Midfielder", "Midfielder", "Fullback", "Center-back"]
JS = """return Array.from(document.querySelectorAll("a[aria-label^='#']")).map(a => {
  const img = a.querySelector("img[src*='teamlogo']");
  return {href: a.getAttribute('href'), text: a.innerText, crest: img ? img.getAttribute('src') : null};
});"""

def num(s):
    try:
        return float(str(s).replace(",", "").replace("%", "").strip())
    except ValueError:
        return None

def read_rows(driver):
    out = []
    for d in driver.execute_script(JS):
        m = re.search(r"/players/(\d+)", d["href"] or "")
        lines = [l.strip() for l in (d["text"] or "").split("\n") if l.strip()]
        if not m or len(lines) < 3:
            continue
        t = re.search(r"teamlogo/(\d+)", d["crest"] or "")
        out.append({"id": int(m.group(1)), "name": lines[1],
                    "teamId": int(t.group(1)) if t else None,
                    "value": num(lines[-1]),
                    "sub": num(lines[2].rsplit(":", 1)[-1]) if len(lines) >= 4 else None})
    return out

def wait_rows(driver):
    WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, ROWS)))
    last = -1
    for _ in range(15):
        n = driver.execute_script("return document.querySelectorAll(arguments[0]).length", ROWS)
        if n == last:
            break
        last = n
        time.sleep(1)

def load(driver, stat):
    url = URL.format(lg=LEAGUE_ID, se=SEASON_ID, stat=stat, slug=SLUG)
    if not allowed(url):
        print("Blocked by robots.txt:", url)
        return None
    t0 = time.time()
    driver.get(url)
    wait_rows(driver)
    secs = time.time() - t0
    log_request("selenium", url, 200, len(driver.page_source.encode("utf-8")), secs)
    return read_rows(driver), secs

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    others = [s for s in WANTED if s != "mins_played"]
    stats = ["mins_played"] + (others[:limit] if limit else others)

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"--user-agent={UA}")
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(60)

    t0 = time.time()
    players, columns, groups, page_loads = {}, {}, {}, 0
    try:
        for stat in stats:
            res = load(driver, stat)
            page_loads += 1
            if res is None:
                continue
            rows, secs = res
            print(f"  {stat}: {len(rows)} players ({secs:.1f} s)")
            for r in rows:
                players.setdefault(r["id"], {"id": r["id"], "name": r["name"], "teamId": r["teamId"]})
                columns.setdefault(stat, {})[r["id"]] = r["value"]
                if r["sub"] is not None:
                    columns.setdefault(stat + "_sub", {})[r["id"]] = r["sub"]

            if stat == "mins_played":          # page with the most players: read the position filters
                for f in FILTERS:
                    btns = driver.find_elements(By.XPATH, f"//button[normalize-space()='{f}']")
                    if not btns:
                        print(f"  filter {f}: button not found")
                        continue
                    driver.execute_script("arguments[0].click();", btns[0])
                    time.sleep(3)
                    got = read_rows(driver)
                    for r in got:
                        groups[r["id"]] = f
                    print(f"  filter {f}: {len(got)} players")
            time.sleep(2)
    finally:
        driver.quit()

    df = pd.DataFrame(list(players.values())).set_index("id")
    df["position_group"] = pd.Series(groups)
    df["position_group"] = df["position_group"].fillna("no_filter")
    for col, values in columns.items():
        df[col] = pd.Series(values)
    df = df.reset_index()

    out = os.path.join(ROOT, "data", "selenium_data.csv")
    df.to_csv(out, index=False)

    print("\n=== SUMMARY (SELENIUM) ===")
    print(f"players: {len(df)} | columns: {df.shape[1]}")
    print(df["position_group"].value_counts().to_string())
    print(f"page loads: {page_loads} | time: {time.time() - t0:.1f} s")
    print("saved:", out)

if __name__ == "__main__":
    main()
