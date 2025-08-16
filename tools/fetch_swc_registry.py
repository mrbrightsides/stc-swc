#!/usr/bin/env python3
"""
Robust SWC registry fetcher (tanpa pakai GitHub "contents" listing).
Langsung tarik raw JSON untuk SWC-100..SWC-199 dari branch master/main.

Output:
  stc_swc/normalize/swc_registry_full.json
"""
from pathlib import Path
import os, json, requests, sys

OUT_PATH = Path("stc_swc/normalize/swc_registry_full.json")
OWNER = "SmartContractSecurity"
REPO = "SWC-registry"
BRANCHES = ["master", "main"]        # coba master dulu, lalu main
ID_RANGE = range(100, 200)           # kalau perlu perlebar rentangnya

def _session():
    s = requests.Session()
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        s.headers["Authorization"] = f"Bearer {tok}"
    s.headers["User-Agent"] = "stc-swc-fetcher"
    return s

def fetch_all():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    s = _session()
    entries = {}
    ok = 0

    for swc_id in ID_RANGE:
        name = f"SWC-{swc_id}"
        data = None

        for br in BRANCHES:
            url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{br}/entries/{name}/{name}.json"
            try:
                r = s.get(url, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    break
            except Exception as e:
                print(f"[warn] {name} on {br}: {e}", file=sys.stderr)

        if not data:
            continue  # file nggak ada / ID belum dipakai

        key = str(data.get("SWC-ID") or swc_id)
        entries[key] = {
            "id": data.get("SWC-ID") or key,
            "title": data.get("Title"),
            "severity": data.get("Severity"),
            "description": data.get("Description"),
            "remediation": data.get("Remediation") or data.get("Mitigation"),
            "relationships": data.get("Relationships"),
            "cwe": data.get("CWE"),
            "references": data.get("References"),
        }
        ok += 1
        if ok % 10 == 0:
            print(f"[info] fetched {ok} entries...", file=sys.stderr)

    OUT_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ wrote {OUT_PATH} with {len(entries)} entries")

if __name__ == "__main__":
    fetch_all()
