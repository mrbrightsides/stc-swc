#!/usr/bin/env python3
"""
Fetch all SWC registry entries and build a local cache.

Output:
  stc_swc/normalize/swc_registry_full.json
"""
from pathlib import Path
import os, json, base64, requests, sys

API_DIRS = "https://api.github.com/repos/SmartContractSecurity/SWC-registry/contents/entries?ref=main"
API_FILE = "https://api.github.com/repos/SmartContractSecurity/SWC-registry/contents/entries/{name}/{name}.json?ref=main"
OUT_PATH = Path("stc_swc/normalize/swc_registry_full.json")

def _session():
    s = requests.Session()
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        s.headers["Authorization"] = f"Bearer {tok}"
    s.headers["User-Agent"] = "stc-swc-fetcher"
    s.headers["Accept"] = "application/vnd.github+json"
    return s

def fetch_all():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    s = _session()

    # list directories under entries/
    r = s.get(API_DIRS, timeout=30)
    r.raise_for_status()
    items = r.json()
    dirs = [it["name"] for it in items if it.get("type") == "dir" and it.get("name","").startswith("SWC-")]
    print(f"[info] found {len(dirs)} SWC dirs", file=sys.stderr)

    entries = {}
    for name in dirs:
        url = API_FILE.format(name=name)  # entries/SWC-107/SWC-107.json
        try:
            fr = s.get(url, timeout=30)
            fr.raise_for_status()
            content = fr.json().get("content", "")
            data = json.loads(base64.b64decode(content).decode("utf-8"))
        except Exception as e:
            print(f"[warn] skip {name}: {e}", file=sys.stderr)
            continue

        key = str(data.get("SWC-ID") or name.replace("SWC-", ""))
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
