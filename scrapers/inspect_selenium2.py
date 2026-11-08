import time
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
driver = webdriver.Chrome(options=opts)

def rows():
    return driver.find_elements(By.CSS_SELECTOR, ROWS)

t0 = time.time()
driver.get(URL)
WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, ROWS)))
print("first rows visible after:", round(time.time() - t0, 1), "s")
print("rows before scrolling:", len(rows()))

last = -1
for i in range(15):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1.5)
    n = len(rows())
    print(f"after scroll {i + 1}: {n} rows")
    if n == last:
        break
    last = n

print("\nfirst 3 rows:")
for r in rows()[:3]:
    crest = [i.get_attribute("src") for i in r.find_elements(By.CSS_SELECTOR, "img[src*='teamlogo']")]
    print(" label:", r.get_attribute("aria-label"))
    print(" href :", r.get_attribute("href"))
    print(" crest:", crest[:1])
    print(" text :", repr(r.text[:100]))

print("\nbuttons on the page:")
texts = [b.text.strip() for b in driver.find_elements(By.TAG_NAME, "button") if 0 < len(b.text.strip()) < 30]
print(texts[:25])

els = driver.find_elements(By.XPATH, "//*[normalize-space(text())='Striker']")
print("\n'Striker' filter elements found:", [e.tag_name for e in els])
if els:
    before = len(rows())
    driver.execute_script("arguments[0].click();", els[0])
    time.sleep(3)
    r2 = rows()
    print(f"rows before click: {before} | after clicking Striker: {len(r2)}")
    print("first after click:", [r.get_attribute("aria-label") for r in r2[:3]])
driver.quit()
