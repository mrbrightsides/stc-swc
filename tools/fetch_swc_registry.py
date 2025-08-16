#!/usr/bin/env python3
"""
Fetch all SWC registry entries from the official GitHub repo and build a local cache.

Output:
  stc_swc/normalize/swc_registry_full.json   # dict keyed by '107', '103', ...

Tips:
  - Set env GITHUB_TOKEN to raise rate limits (optional).
  - Safe to run multiple times; it overwrites the cache file.
"""
from pathlib import Path
import os, json, requests, sys

API_LIST = "https://api.github.com/repos/SmartContractSecurity/SWC-registry/contents/entries"
RAW_BASE = "https://raw.githubusercontent.com/SmartContractSecurity/SWC-registry/master/entries"

OUT_PATH = Path("stc_swc/normalize/swc_registry_full.json")  # <-- target cache

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

    r = s.get(API_LIST, timeout=30)
    r.raise_for_status()
    items = r.json()

    entries = {}
    for it in items:
        name = it.get("name", "")
        if not name.endswith(".json"):  # skip non-json
            continue
        # Example: SWC-107.json -> "107"
        key = name.replace("SWC-", "").replace(".json", "")
        url = f"{RAW_BASE}/{name}"
        try:
            jr = s.get(url, timeout=30)
            jr.raise_for_status()
            data = jr.json()
        except Exception as e:
            print(f"skip {name}: {e}", file=sys.stderr)
            continue

        # Normalize a compact record we actually use
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

    OUT_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ wrote {OUT_PATH} with {len(entries)} entries")

if __name__ == "__main__":
    fetch_all()
