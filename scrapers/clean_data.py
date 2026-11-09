import os, sys
import pandas as pd
from common import ROOT

MIN_MINUTES = int(sys.argv[1]) if len(sys.argv) > 1 else 270

api = pd.read_csv(os.path.join(ROOT, "data", "api_data.csv"))
sel = pd.read_csv(os.path.join(ROOT, "data", "selenium_data.csv"))[["id", "position_group"]]
df = api.merge(sel, on="id", how="left")
print("players at start:", len(df), "| duplicate ids:", int(df["id"].duplicated().sum()))
df = df.drop_duplicates("id")

# ---------- 1. the four labels ----------
CODE_GROUPS = {"GK": [11],
               "DF": [32, 33, 34, 35, 36, 37, 38, 51],
               "MF": [64, 66, 73, 74, 75, 76, 77, 78, 85],
               "FW": [83, 84, 87, 103, 105, 106, 107, 115]}
CODE_MAP = {c: g for g, codes in CODE_GROUPS.items() for c in codes}
GROUP_MAP = {"Striker": "FW", "Winger": "FW", "Attacking Midfielder": "MF",
             "Midfielder": "MF", "Fullback": "DF", "Center-back": "DF"}
df["from_code"] = df["position"].map(CODE_MAP)
df["from_group"] = df["position_group"].map(GROUP_MAP)
df["label"] = df["from_code"].fillna(df["from_group"])

print("\n=== 1. LABELS ===")
print("label from the code:", int(df["from_code"].notna().sum()))
print("label from Selenium's group (codes not mapped):", int((df["from_code"].isna() & df["from_group"].notna()).sum()))
nolabel = df[df["label"].isna()]
print("no label, removed:", len(nolabel))
print(nolabel[["name", "position", "mins_played"]].to_string(index=False))
both = df["from_code"].notna() & df["from_group"].notna()
print("code and group disagree:", int((df.loc[both, "from_code"] != df.loc[both, "from_group"]).sum()), "of", int(both.sum()))
df = df[df["label"].notna()].copy()

# ---------- 2. minimum minutes ----------
df["minutes"] = df["mins_played"]
print("\n=== 2. MINUTES ===")
print("class counts before the filter:", df["label"].value_counts().to_dict())
for lim in (90, 180, 270, 450):
    print(f"  with at least {lim} minutes:", int((df["minutes"] >= lim).sum()))
df = df[df["minutes"] >= MIN_MINUTES].copy()
print(f"kept players with at least {MIN_MINUTES} minutes:", len(df))
print("class counts after the filter:", df["label"].value_counts().to_dict())

# ---------- 3. features, all 'per 90 minutes' ----------
ALREADY_P90 = {"shots_p90": "total_scoring_att", "shots_on_target_p90": "ontarget_scoring_att",
               "dribbles_p90": "won_contest", "passes_p90": "accurate_pass",
               "long_balls_p90": "accurate_long_balls", "tackles_p90": "total_tackle",
               "interceptions_p90": "interception", "clearances_p90": "effective_clearance",
               "blocks_p90": "outfielder_block", "recoveries_p90": "ball_recovery",
               "won_in_final_third_p90": "poss_won_att_3rd", "fouls_p90": "fouls",
               "saves_p90": "saves", "goals_conceded_p90": "goals_conceded",
               "chances_created_p90": "total_att_assist_sub"}
TOTALS = {"goals_p90": "goals", "assists_p90": "goal_assist", "xg_p90": "expected_goals",
          "xa_p90": "expected_assists", "big_chances_p90": "big_chance_created",
          "yellow_p90": "yellow_card", "red_p90": "red_card",
          "pen_won_p90": "penalty_won", "pen_conceded_p90": "penalty_conceded",
          "clean_sheet_rate": "clean_sheet"}
RATES = {"pass_accuracy": "accurate_pass_sub", "long_ball_accuracy": "accurate_long_balls_sub",
         "dribble_success": "won_contest_sub", "shot_conversion": "total_scoring_att_sub"}

print("\n=== 3. EMPTY CELLS (players with >= 450 minutes, before filling) ===")
big = df[df["minutes"] >= 450]
src = list(ALREADY_P90.values()) + list(TOTALS.values()) + list(RATES.values())
blank = (big[src].isna().mean() * 100).round(0).sort_values(ascending=False)
print(blank[blank > 0].head(10).to_string())

out = df[["id", "name", "teamId", "position", "position_group", "label", "minutes"]].copy()
out = out.rename(columns={"position": "position_code", "label": "position"})
for new, col in ALREADY_P90.items():
    out[new] = df[col].fillna(0)
for new, col in TOTALS.items():
    out[new] = df[col].fillna(0) / df["minutes"] * 90
for new, col in RATES.items():
    out[new] = df[col]
    out[new] = out[new].fillna(out[new].median())

features = list(ALREADY_P90) + list(TOTALS) + list(RATES)
out[features] = out[features].round(3)

# ---------- 4. save and check ----------
path = os.path.join(ROOT, "data", "clean_data.csv")
out.to_csv(path, index=False)
print("\n=== 4. RESULT ===")
print("rows:", len(out), "| features:", len(features), "| empty cells left:", int(out[features].isna().sum().sum()))
print(out["position"].value_counts().to_string())
print("\naverage per position (sanity check):")
show = ["tackles_p90", "interceptions_p90", "clearances_p90", "passes_p90",
        "shots_p90", "goals_p90", "saves_p90"]
print(out.groupby("position")[show].mean().round(2).to_string())
print("\nsaved:", path)
