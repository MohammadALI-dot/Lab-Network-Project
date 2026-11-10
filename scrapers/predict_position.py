import os, sys
import joblib
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
saved = joblib.load(os.path.join(ROOT, "models", "position_model.joblib"))
model, features, medians = saved["model"], saved["features"], saved["medians"]
RATES = ["pass_accuracy", "long_ball_accuracy", "dribble_success", "shot_conversion"]

ASK = [("goals_p90", "Goals per 90 minutes"),
       ("assists_p90", "Assists per 90 minutes"),
       ("shots_p90", "Shots per 90"),
       ("shots_on_target_p90", "Shots on target per 90"),
       ("dribbles_p90", "Successful dribbles per 90"),
       ("passes_p90", "Accurate passes per 90"),
       ("pass_accuracy", "Pass accuracy in % (0-100)"),
       ("tackles_p90", "Tackles per 90"),
       ("interceptions_p90", "Interceptions per 90"),
       ("clearances_p90", "Clearances per 90"),
       ("fouls_p90", "Fouls committed per 90"),
       ("saves_p90", "Saves per 90 (goalkeepers)")]

def suggest(stats):
    row = pd.DataFrame([{f: stats.get(f, medians[f] if f in RATES else 0.0) for f in features}])
    proba = pd.Series(model.predict_proba(row)[0], index=model.classes_).sort_values(ascending=False)
    return proba

stats = {}
if len(sys.argv) > 1:                       # example: python predict_position.py tackles_p90=2 passes_p90=45
    for a in sys.argv[1:]:
        k, v = a.split("=")
        if k not in features:
            sys.exit(f"Unknown statistic '{k}'. Valid names: {', '.join(features)}")
        stats[k] = float(v)
else:
    print("Enter the player's statistics PER 90 MINUTES. Press Enter to skip (counts as 0).\n")
    for key, label in ASK:
        v = input(f"{label}: ").strip()
        if v:
            stats[key] = float(v)

p = suggest(stats)
names = {"GK": "Goalkeeper", "DF": "Defender", "MF": "Midfielder", "FW": "Forward"}
print(f"\nSuggested position: {p.index[0]} ({names[p.index[0]]})")
print("How sure the model is:")
for pos, v in p.items():
    print(f"  {pos}: {v * 100:5.1f}%  " + "#" * int(v * 30))
