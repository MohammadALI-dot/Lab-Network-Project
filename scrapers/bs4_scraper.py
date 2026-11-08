import json, os, sys, time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from common import polite_get, ROOT

LEAGUE_ID, SEASON_ID, SLUG = 87, 38843, "laliga"
URL = "https://www.fotmob.com/leagues/{lg}/stats/season/{se}/players/{stat}/{slug}"

WANTED = [
    "goals", "goal_assist", "total_scoring_att", "ontarget_scoring_att",
    "expected_goals", "expected_assists", "big_chance_created", "total_att_assist",
    "won_contest", "accurate_pass", "accurate_long_balls",
    "total_tackle", "interception", "effective_clearance", "outfielder_block",
    "ball_recovery", "poss_won_att_3rd", "fouls", "yellow_card", "red_card",
    "saves", "clean_sheet", "goals_conceded", "penalty_won", "penalty_conceded",
    "mins_played",
]

def fetch(session, stat):
    r = polite_get(session, URL.format(lg=LEAGUE_ID, se=SEASON_ID, stat=stat, slug=SLUG), method="bs4")
    if r is None or r.status_code != 200:
        print(f"  {stat}: failed (status {getattr(r, 'status_code', None)})")
        return None, 0
    soup = BeautifulSoup(r.text, "lxml")
    tag = soup.find("script", id="__NEXT_DATA__")
    if tag is None:
        print(f"  {stat}: no embedded data found")
        return None, len(r.content)
    return json.loads(tag.string)["props"]["pageProps"]["data"], len(r.content)

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    session = requests.Session()
    t0 = time.time()
    requests_made, total_bytes = 0, 0

    # first page also tells us which stat names really exist
    first, nb = fetch(session, "goals")
    requests_made += 1; total_bytes += nb
    if first is None:
        sys.exit("Could not load the first page. Stopping.")
    titles = {s["name"]: s["title"] for s in first["statsList"]}
    wanted = [s for s in WANTED if s in titles]
    print("Not available on the site (skipped):", [s for s in WANTED if s not in titles])
    if limit:
        wanted = wanted[:limit]

    players, columns, meta = {}, {}, []
    pages = {"goals": first}
    for stat in wanted:
        d = pages.get(stat)
        if d is None:
            d, nb = fetch(session, stat)
            requests_made += 1; total_bytes += nb
        if d is None:
            continue
        rows = d["statsData"]
        meta.append({"stat": stat, "title": titles[stat],
                     "substat_title": d.get("substatTitle"), "players": len(rows)})
        print(f"  {stat}: {len(rows)} players")
        for p in rows:
            pid = p["id"]
            info = players.setdefault(pid, {"id": pid, "name": p["name"],
                                            "teamId": p["teamId"], "position": p.get("position")})
            if info["position"] is None and p.get("position") is not None:
                info["position"] = p["position"]
            columns.setdefault(stat, {})[pid] = p["statValue"]["value"]
            sub = p.get("substatValue")
            if sub:
                columns.setdefault(stat + "_sub", {})[pid] = sub["value"]

    df = pd.DataFrame(list(players.values())).set_index("id")
    for col, values in columns.items():
        df[col] = pd.Series(values)
    df = df.reset_index()

    out = os.path.join(ROOT, "data", "bs4_data.csv")
    df.to_csv(out, index=False)
    pd.DataFrame(meta).to_csv(os.path.join(ROOT, "data", "bs4_stat_meta.csv"), index=False)

    secs = time.time() - t0
    print("\n=== SUMMARY (BS4) ===")
    print(f"players: {len(df)} | columns: {df.shape[1]}")
    print(f"players without position: {df['position'].isna().sum()}")
    print(f"page requests: {requests_made} | bytes downloaded: {total_bytes:,} | time: {secs:.1f} s")
    print("saved:", out)

if __name__ == "__main__":
    main()
