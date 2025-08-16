#!/usr/bin/env python3
"""
Fetch all SWC registry entries and build a local cache.

Output:
  stc_swc/normalize/swc_registry_full.json
"""
from pathlib import Path
import os, json, base64, requests, sys

OWNER = "SmartContractSecurity"
REPO  = "SWC-registry"

API_REPO   = f"https://api.github.com/repos/{OWNER}/{REPO}"
API_DIRS   = f"{API_REPO}/contents/entries"                    # + ?ref={branch}
API_FILE   = f"{API_REPO}/contents/entries/{{name}}/{{name}}.json"  # + ?ref={branch}
OUT_PATH   = Path("stc_swc/normalize/swc_registry_full.json")

def _session():
    s = requests.Session()
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        s.headers["Authorization"] = f"Bearer {tok}"
    s.headers["User-Agent"] = "stc-swc-fetcher"
    s.headers["Accept"] = "application/vnd.github+json"
    return s

def _get_default_branch(s: requests.Session) -> str:
    r = s.get(API_REPO, timeout=30)
    r.raise_for_status()
    return r.json().get("default_branch", "master")

def _get_json_file(s: requests.Session, url_base: str, branch: str) -> dict | None:
    """GET contents API for a file and decode base64 content. Try branch; return dict or None."""
    try:
        r = s.get(f"{url_base}?ref={branch}", timeout=30)
        r.raise_for_status()
        js = r.json()
        if isinstance(js, dict) and js.get("content"):
            return json.loads(base64.b64decode(js["content"]).decode("utf-8"))
        # When API returns direct JSON (rare), pass through:
        if isinstance(js, dict) and all(k in js for k in ("Title", "SWC-ID")):
            return js
    except Exception as e:
        print(f"[warn] file fetch failed ({branch}): {e}", file=sys.stderr)
    return None

def fetch_all():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    s = _session()

    # 1) determine default branch
    default_branch = _get_default_branch(s)
    alt_branch = "main" if default_branch == "master" else "master"
    print(f"[info] default branch: {default_branch}", file=sys.stderr)

    # 2) list directories under entries/
    def list_dirs(branch: str):
        r = s.get(f"{API_DIRS}?ref={branch}", timeout=30)
        r.raise_for_status()
        items = r.json()
        return [it["name"] for it in items if it.get("type")=="dir" and it.get("name","").startswith("SWC-")]

    try:
        dirs = list_dirs(default_branch)
    except Exception as e:
        print(f"[warn] list dirs failed on {default_branch}: {e}", file=sys.stderr)
        dirs = list_dirs(alt_branch)

    print(f"[info] found {len(dirs)} SWC dirs", file=sys.stderr)

    # 3) fetch each SWC-xxx.json (try default branch then fallback)
    entries = {}
    for name in dirs:
        url = API_FILE.format(name=name)
        data = _get_json_file(s, url, default_branch) or _get_json_file(s, url, alt_branch)
        if not data:
            print(f"[warn] skip {name}: cannot fetch JSON", file=sys.stderr)
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
