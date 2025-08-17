import json
from pathlib import Path

def write_ndjson(rows: list[dict], path: str, mode="full"):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    FIELDS_FULL = [
        "finding_id", "timestamp", "network", "contract", "file", "line_start", "line_end",
        "swc_id", "title", "severity", "confidence", "status", "remediation", "commit_hash"
    ]
    FIELDS_SHORT = [
        "swc_id", "title", "description", "severity", "tool", "contract", "function", "file", "line", "timestamp"
    ]
    FIELDS = FIELDS_FULL if mode == "full" else FIELDS_SHORT

    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            obj = {k: r.get(k, "") for k in FIELDS}
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
