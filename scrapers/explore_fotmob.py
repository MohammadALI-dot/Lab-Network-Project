import requests, time
BASE = "https://data.fotmob.com/stats/87/season/38843/"
H = {"User-Agent": "Mozilla/5.0 (student project)"}
for stat in ["accurate_pass", "total_tackle", "interception", "goals", "saves"]:
    r = requests.get(BASE + stat + ".json", headers=H, timeout=30)
    for t in r.json()["TopLists"]:
        players = t["StatList"]
        pos = sorted({p for x in players for p in x.get("Positions", [])})
        print(f"{stat}: status {r.status_code}, {len(players)} players, position ids: {pos}")
    time.sleep(2)
