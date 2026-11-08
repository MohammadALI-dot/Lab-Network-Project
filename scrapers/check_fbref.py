import re, requests
from bs4 import BeautifulSoup, Comment

url = "https://fbref.com/en/comps/12/stats/La-Liga-Stats"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (student project)"}, timeout=30)
print("status:", r.status_code, "| bytes:", len(r.content))

soup = BeautifulSoup(r.text, "lxml")
html = r.text
for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
    html += str(c)
soup = BeautifulSoup(html, "lxml")

for t in soup.find_all("table"):
    cols = [th.get("data-stat") for th in t.select("thead tr:last-child th")]
    print("\nTABLE:", t.get("id"))
    print(cols)
