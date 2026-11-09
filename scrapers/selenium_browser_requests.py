import json, time
from collections import Counter
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common import allowed, UA

URL = "https://www.fotmob.com/leagues/87/stats/season/38843/players/goals/laliga"
ROWS = "a[aria-label^='#']"
if not allowed(URL):
    raise SystemExit("Blocked by robots.txt")

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument(f"--user-agent={UA}")
opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
driver = webdriver.Chrome(options=opts)
driver.get(URL)
WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, ROWS)))
time.sleep(3)

reqs, sent_bytes, types, hosts = 0, 0, Counter(), Counter()
for e in driver.get_log("performance"):
    m = json.loads(e["message"])["message"]
    if m["method"] == "Network.requestWillBeSent":
        reqs += 1
        types[m["params"].get("type", "?")] += 1
        hosts[urlparse(m["params"]["request"]["url"]).netloc] += 1
    elif m["method"] == "Network.loadingFinished":
        sent_bytes += m["params"].get("encodedDataLength", 0)
driver.quit()

print("browser requests for ONE page:", reqs)
print("bytes transferred (compressed):", sent_bytes, "=", round(sent_bytes / 1024, 1), "KB")
print("by type:", dict(types))
print("top hosts:", hosts.most_common(8))
