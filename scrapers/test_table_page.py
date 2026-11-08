import sys, json, requests
from bs4 import BeautifulSoup

url = sys.argv[1]
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (student project)"}, timeout=30)
print("status:", r.status_code, "| bytes:", len(r.content), "| final url:", r.url)

for name in ["Raphinha", "Budimir", "Zabiri"]:
    print(f"'{name}' appears {r.text.count(name)} times in the raw HTML")

soup = BeautifulSoup(r.text, "lxml")
tag = soup.find("script", id="__NEXT_DATA__")
print("__NEXT_DATA__ present:", tag is not None)
if tag:
    data = json.loads(tag.string)
    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, list) and len(v) > 20:
                    print(f"{path}/{k}: list of {len(v)} items")
                walk(v, f"{path}/{k}")
        elif isinstance(o, list):
            for v in o[:2]:
                walk(v, path)
    walk(data)
