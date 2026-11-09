import os
import pandas as pd
from common import ROOT

def load(f):
    return pd.read_csv(os.path.join(ROOT, "data", f))

b, a, s = load("bs4_data.csv"), load("api_data.csv"), load("selenium_data.csv")
sets = {"bs4": set(b["id"]), "api": set(a["id"]), "selenium": set(s["id"])}

print("=== 1. Players ===")
print({k: len(v) for k, v in sets.items()})
print("in all three:", len(sets["bs4"] & sets["api"] & sets["selenium"]))
for x, y in [("bs4", "api"), ("bs4", "selenium"), ("api", "selenium")]:
    print(f"{x} vs {y}: only in {x}: {len(sets[x] - sets[y])} | only in {y}: {len(sets[y] - sets[x])}")

def compare(x, y, nx, ny):
    ids = sorted(set(x["id"]) & set(y["id"]))
    xx, yy = x.set_index("id").loc[ids], y.set_index("id").loc[ids]
    skip = ("name", "position", "positions_all", "position_group")
    rows = []
    for c in xx.columns:
        if c in yy.columns and c not in skip:
            p, q = xx[c], yy[c]
            both = p.notna() & q.notna()
            differ = int(((p[both] - q[both]).abs() > 0.06).sum())
            one_only = int((p.notna() != q.notna()).sum())
            rows.append((c, differ, one_only))
    r = pd.DataFrame(rows, columns=["column", "values_differ", "blank_in_one_only"])
    print(f"\n=== {nx} vs {ny}: {len(ids)} common players, {len(r)} common columns ===")
    print("cells that differ:", int(r["values_differ"].sum()),
          "| cells filled in only one:", int(r["blank_in_one_only"].sum()))
    print("worst columns:")
    print(r.sort_values(["values_differ", "blank_in_one_only"], ascending=False).head(6).to_string(index=False))

compare(b, a, "bs4", "api")
compare(b, s, "bs4", "selenium")
compare(a, s, "api", "selenium")

print("\n=== 2. Does Selenium's position group match the codes? ===")
GROUPS = {"GK": [11], "DF": [32, 33, 34, 35, 36, 37, 38, 51],
          "MF": [64, 66, 73, 74, 75, 76, 77, 78, 85],
          "FW": [83, 84, 87, 103, 105, 106, 107, 115]}
MAP = {c: g for g, codes in GROUPS.items() for c in codes}
m = b[["id", "position"]].merge(s[["id", "position_group"]], on="id")
m["group"] = m["position"].map(MAP).fillna("other")
print(pd.crosstab(m["position_group"], m["group"]).to_string())
