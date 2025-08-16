#!/usr/bin/env python3
"""
Fetch all SWC registry entries from the official GitHub repo and build a local cache.

Output:
  stc_swc/normalize/swc_registry_full.json   # dict keyed by '107', '103', ...
"""
from pathlib import Path
import os, json, requests, sys

API_LIST_DIRS = "https://api.github.com/repos/SmartContractSecurity/SWC-registry/contents/entries"
RAW_BASE = "https://raw.githubusercontent.com/SmartContractSecurity/SWC-registry/master/entries"

OUT_PATH = Path("stc_swc/normalize/swc_registry_full.json")

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

    # 1) list entries/ -> returns directories: SWC-100, SWC-101, ...
    r = s.get(API_LIST_DIRS, timeout=30)
    r.raise_for_status()
    items = r.json()

    entries = {}
    for it in items:
        # Only process directories named SWC-xxx
        if it.get("type") != "dir":
            continue
        name = it.get("name") or ""        # e.g., "SWC-107"
        if not name.startswith("SWC-"):
            continue

        json_name = f"{name}.json"         # e.g., "SWC-107.json"
        url = f"{RAW_BASE}/{name}/{json_name}"

        try:
            jr = s.get(url, timeout=30)
            jr.raise_for_status()
            data = jr.json()
        except Exception as e:
            print(f"skip {name}: {e}", file=sys.stderr)
            continue

        key = str(data.get("SWC-ID") or name.replace("SWC-", ""))

        # Normalize minimal fields we need
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
