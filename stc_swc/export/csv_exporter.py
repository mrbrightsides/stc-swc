import csv
from pathlib import Path

FIELDS = [
    "finding_id",
    "timestamp",
    "network",
    "contract",
    "file",
    "line_start",
    "line_end",
    "swc_id",
    "title",
    "severity",
    "confidence",
    "status",
    "remediation",
    "commit_hash"
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
