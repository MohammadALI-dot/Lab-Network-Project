import json, os
import requests
from bs4 import BeautifulSoup
from common import polite_get, ROOT

URL = "https://www.fotmob.com/leagues/87/stats/season/38843/players/goals/laliga"
r = polite_get(requests.Session(), URL, method="explore")

path = os.path.join(ROOT, "data", "samples", "goals_page.html")
open(path, "w", encoding="utf-8").write(r.text)

soup = BeautifulSoup(r.text, "lxml")
data = json.loads(soup.find("script", id="__NEXT_DATA__").string)
d = data["props"]["pageProps"]["data"]

print("keys in data:", list(d.keys()))
print("\nfirst player record:")
print(json.dumps(d["statsData"][0], indent=2)[:1200])
print("\nother keys:")
for k, v in d.items():
    if k != "statsData":
        print(k, "->", str(v)[:200])
