import json
from bs4 import BeautifulSoup

soup = BeautifulSoup(open("fotmob_page.html", encoding="utf-8"), "lxml")
data = json.loads(soup.find("script", id="__NEXT_DATA__").string)
stats = data["props"]["pageProps"]["stats"]
print("keys of stats:", list(stats.keys()) if isinstance(stats, dict) else type(stats))
pl = stats["players"]
print("first item:")
print(json.dumps(pl[0], indent=2)[:800])
