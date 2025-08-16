import json
from pathlib import Path

FIELDS = [
    "swc_id","title","description","severity","tool","contract","function","file","line","timestamp"
]

def write_ndjson(rows: list[dict], path: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            obj = {k: r.get(k, "") for k in FIELDS}
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
