import json
from bs4 import BeautifulSoup

soup = BeautifulSoup(open("fotmob_page.html", encoding="utf-8"), "lxml")
tag = soup.find("script", id="__NEXT_DATA__")
data = json.loads(tag.string)
print("top-level keys:", list(data.keys()))

def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("StatList", "TopLists", "players", "stats"):
                size = len(v) if hasattr(v, "__len__") else "?"
                print(f"{path}/{k}: {size} items")
            walk(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:3]):
            walk(v, f"{path}[{i}]")

walk(data)
