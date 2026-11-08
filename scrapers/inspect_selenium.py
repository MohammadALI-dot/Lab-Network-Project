import os, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from common import allowed, UA, ROOT

URL = "https://www.fotmob.com/leagues/87/stats/season/38843/players/goals/laliga"
if not allowed(URL):
    raise SystemExit("Blocked by robots.txt")

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument(f"--user-agent={UA}")
driver = webdriver.Chrome(options=opts)

t0 = time.time()
driver.get(URL)
time.sleep(5)
print("title:", driver.title, "| load time:", round(time.time() - t0, 1), "s")

html = driver.page_source
open(os.path.join(ROOT, "data", "samples", "selenium_goals_dom.html"), "w", encoding="utf-8").write(html)
print("page source bytes:", len(html))
print("'Raphinha' appears:", html.count("Raphinha"), "times")

links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/players/']")
print("player links:", len(links))
for a in links[:2]:
    print("\n--- link html ---")
    print(a.get_attribute("outerHTML")[:700])
driver.quit()
