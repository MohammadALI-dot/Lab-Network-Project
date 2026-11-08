import os, sys, time
import pandas as pd
import requests
from common import polite_get, ROOT
from bs4_scraper import WANTED, LEAGUE_ID, SEASON_ID

URL = "https://data.fotmob.com/stats/{lg}/season/{se}/{stat}.json"

def fetch(session, stat):
    r = polite_get(session, URL.format(lg=LEAGUE_ID, se=SEASON_ID, stat=stat), method="api")
    if r is None or r.status_code != 200:
        print(f"  {stat}: failed (status {getattr(r, 'status_code', None)})")
        return None, 0
    try:
        rows = r.json()["TopLists"][0]["StatList"]
    except Exception as e:
        print(f"  {stat}: unexpected format ({e})")
        return None, len(r.content)
    return rows, len(r.content)

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    stats = WANTED[:limit] if limit else WANTED
    session = requests.Session()
    t0 = time.time()
    requests_made, total_bytes = 0, 0
    players, columns = {}, {}

    for stat in stats:
        rows, nb = fetch(session, stat)
        requests_made += 1; total_bytes += nb
        if rows is None:
            continue
        print(f"  {stat}: {len(rows)} players")
        for p in rows:
            pid = p.get("ParticiantId", p.get("ParticipantId"))
            info = players.setdefault(pid, {"id": pid, "name": p["ParticipantName"],
                                            "teamId": p["TeamId"], "position": None,
                                            "positions_all": None})
            pos = p.get("Positions") or []
            if pos and info["position"] is None:
                info["position"] = pos[0]
                info["positions_all"] = "|".join(str(x) for x in pos)
            columns.setdefault(stat, {})[pid] = p["StatValue"]
            if p.get("SubStatValue") is not None:
                columns.setdefault(stat + "_sub", {})[pid] = p["SubStatValue"]

    df = pd.DataFrame(list(players.values())).set_index("id")
    for col, values in columns.items():
        df[col] = pd.Series(values)
    df = df.reset_index()

    out = os.path.join(ROOT, "data", "api_data.csv")
    df.to_csv(out, index=False)

    secs = time.time() - t0
    print("\n=== SUMMARY (API) ===")
    print(f"players: {len(df)} | columns: {df.shape[1]}")
    print(f"players without position: {df['position'].isna().sum()}")
    print(f"requests: {requests_made} | bytes downloaded: {total_bytes:,} | time: {secs:.1f} s")
    print("saved:", out)

if __name__ == "__main__":
    main()
