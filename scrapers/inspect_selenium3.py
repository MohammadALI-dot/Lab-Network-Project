import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common import allowed, UA

URL = "https://www.fotmob.com/leagues/87/stats/season/38843/players/mins_played/laliga"
ROWS = "a[aria-label^='#']"
FILTERS = ["Striker", "Winger", "Attacking Midfielder", "Midfielder", "Fullback", "Center-back"]
if not allowed(URL):
    raise SystemExit("Blocked by robots.txt")

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument(f"--user-agent={UA}")
driver = webdriver.Chrome(options=opts)

def rows():
    return driver.find_elements(By.CSS_SELECTOR, ROWS)

t0 = time.time()
driver.get(URL)
WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ROWS)))
time.sleep(2)
print("page ready after:", round(time.time() - t0, 1), "s")
print("rows with filter All:", len(rows()))
print("first 2 rows:", [r.get_attribute("aria-label") for r in rows()[:2]])
print("row text sample:", repr(rows()[0].text[:100]))

seen, total = {}, 0
for f in FILTERS:
    btns = driver.find_elements(By.XPATH, f"//button[normalize-space()='{f}']")
    if not btns:
        print(f"{f}: button not found")
        continue
    driver.execute_script("arguments[0].click();", btns[0])
    time.sleep(3)
    hrefs = [r.get_attribute("href") for r in rows()]
    print(f"{f}: {len(hrefs)} rows | first: {[r.get_attribute('aria-label') for r in rows()[:2]]}")
    for h in hrefs:
        seen.setdefault(h, []).append(f)
    total += len(hrefs)

print("\nsum of rows over all filters:", total)
print("distinct players found by filters:", len(seen))
print("players listed under more than one filter:", sum(1 for v in seen.values() if len(v) > 1))
driver.quit()
