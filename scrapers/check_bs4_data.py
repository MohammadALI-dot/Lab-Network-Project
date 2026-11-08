import os
import pandas as pd
from common import ROOT

df = pd.read_csv(os.path.join(ROOT, "data", "bs4_data.csv"))
print("rows, columns:", df.shape)
print("duplicate player ids:", df["id"].duplicated().sum())

print("\nPreview:")
print(df[["name", "position", "goals", "goal_assist", "total_tackle",
          "interception", "accurate_pass", "mins_played"]].head(8).to_string(index=False))

print("\nMost incomplete columns (% missing):")
print((df.isna().mean() * 100).round(0).sort_values(ascending=False).head(12).to_string())

print("\nPlayers per position code (most-used players listed):")
for code, g in df.groupby("position"):
    top = g.sort_values("mins_played", ascending=False)["name"].head(4).tolist()
    n_gk = g["saves"].notna().sum()
    print(f"code {int(code):>3}: {len(g):>3} players, {n_gk:>2} with saves | {', '.join(top)}")
