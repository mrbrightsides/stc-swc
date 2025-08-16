import csv
from pathlib import Path

FIELDS = [
    "swc_id","title","description","severity","tool","contract","function","file","line","timestamp"
]

def write_csv(rows: list[dict], path: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            # pastikan hanya field yang terdaftar
            w.writerow({k: r.get(k, "") for k in FIELDS})
