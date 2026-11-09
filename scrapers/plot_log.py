import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import ROOT

s = pd.read_csv(os.path.join(ROOT, "network", "metrics_summary.csv"), index_col=0)
fig, ax = plt.subplots(1, 3, figsize=(13, 4))
for a, col, title in zip(ax, ["time_s", "bandwidth_KB", "avg_latency_ms"],
                         ["Total time (s)", "Bandwidth on the wire (KB, log scale)", "Average latency (ms)"]):
    a.bar(s.index, s[col], color=["#4472C4", "#70AD47", "#ED7D31"][:len(s)])
    if col == "bandwidth_KB":
        a.set_yscale("log")
    a.set_title(title)
    for i, v in enumerate(s[col]):
        a.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(ROOT, "network", "comparison_log.png"), dpi=150)
print("saved network/comparison_log.png")
