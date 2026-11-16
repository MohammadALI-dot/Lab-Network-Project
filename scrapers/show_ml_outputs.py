import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cells = json.load(open(os.path.join(ROOT, "notebooks", "ml_analysis.ipynb"), encoding="utf-8"))["cells"]
want = sys.argv[1] if len(sys.argv) > 1 else None          # for example: 7.3

start = next((i for i, c in enumerate(cells)
              if c["cell_type"] == "markdown" and "## 7. Train and test the models" in "".join(c["source"])), None)
if start is None:
    sys.exit("Section 7 not found: run  python scrapers/add_ml_cells.py  and execute the notebook first.")

show = want is None
for c in cells[start:]:
    if c["cell_type"] == "markdown":
        title = "".join(c["source"]).strip().split("\n")[0]
        show = want is None or want in title
        if show:
            print("\n" + "=" * 70 + "\n" + title.lstrip("# ") + "\n" + "=" * 70)
        continue
    if not show:
        continue
    for o in c.get("outputs", []):
        kind = o.get("output_type")
        if kind == "stream":
            print("".join(o["text"]), end="")
        elif kind in ("execute_result", "display_data"):
            d = o.get("data", {})
            if "image/png" in d:
                print("[figure: use the PNG file in report/figures]")
            elif "text/plain" in d:
                print("".join(d["text/plain"]))
