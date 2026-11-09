import os, subprocess
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import ROOT

NET = os.path.join(ROOT, "network")
M = os.path.join(NET, "measure")
times = pd.read_csv(os.path.join(M, "times.csv"))
log = pd.read_csv(os.path.join(NET, "request_log.csv"))

def pcap_stats(path):
    out = subprocess.run(["tshark", "-r", path, "-T", "fields", "-e", "frame.len", "-e", "tcp.stream"],
                         capture_output=True, text=True).stdout
    nbytes, packets, streams = 0, 0, set()
    for line in out.splitlines():
        parts = line.split("\t")
        if not parts[0].strip():
            continue
        nbytes += int(parts[0].split(",")[0])
        packets += 1
        if len(parts) > 1 and parts[1].strip():
            streams.add(parts[1])
    return nbytes, packets, len(streams)

rows = []
for _, t in times.iterrows():
    m, r = t["method"], int(t["run"])
    sub = log.iloc[int(t["log_from"]):int(t["log_to"])]
    own = sub[sub["method"] == m]
    nbytes, packets, conns = pcap_stats(os.path.join(NET, "pcap", f"{m}_run{r}.pcap"))
    cpath = os.path.join(M, f"{m}_run{r}_conn.csv")
    peak = pd.read_csv(cpath, header=None)[1].max() if os.path.exists(cpath) else None
    rows.append({"method": m, "run": r,
                 "time_s": round(t["seconds"], 1),
                 "bandwidth_KB": round(nbytes / 1024, 1),
                 "packets": packets,
                 "tcp_connections": conns,
                 "peak_open_connections": peak,
                 "page_requests": len(own),
                 "all_logged_requests": len(sub),
                 "avg_latency_ms": round(own["seconds"].mean() * 1000, 1),
                 "logged_body_KB": round(own["bytes"].sum() / 1024, 1)})

runs = pd.DataFrame(rows)
runs.to_csv(os.path.join(NET, "metrics.csv"), index=False)
order = [m for m in ["bs4", "api", "selenium"] if m in set(runs["method"])]
summary = runs.groupby("method").mean(numeric_only=True).drop(columns="run").reindex(order).round(1)
summary.to_csv(os.path.join(NET, "metrics_summary.csv"))

print("=== PER RUN ===")
print(runs.to_string(index=False))
print("\n=== SUMMARY (average of runs) ===")
print(summary.to_string())

fig, ax = plt.subplots(2, 2, figsize=(10, 7))
for a, col, title in zip(ax.flat,
        ["time_s", "bandwidth_KB", "page_requests", "avg_latency_ms"],
        ["Total time (s)", "Bandwidth on the wire (KB)", "Page requests (log)", "Average latency (ms)"]):
    a.bar(summary.index, summary[col], color=["#4472C4", "#70AD47", "#ED7D31"][:len(summary)])
    a.set_title(title)
    for i, v in enumerate(summary[col]):
        a.text(i, v, f"{v:g}", ha="center", va="bottom", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(NET, "comparison.png"), dpi=150)
print("\nsaved network/metrics.csv, network/metrics_summary.csv, network/comparison.png")
