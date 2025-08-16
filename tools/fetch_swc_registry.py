#!/usr/bin/env python3
"""
SWC Registry fetcher via GitHub Tree + Blob API (tanpa raw.githubusercontent.com).

- Ambil default_branch
- GET /git/trees/{branch}?recursive=1 untuk list semua file
- Ambil semua path entries/SWC-xxx/README.md
- GET /git/blobs/{sha} untuk konten (base64) lalu parse Markdown

Env opsional: GITHUB_TOKEN  (naikkan rate limit)

Output:
  stc_swc/normalize/swc_registry_full.json
"""
from pathlib import Path
import os, re, json, base64, requests, sys

OWNER = "SmartContractSecurity"
REPO  = "SWC-registry"
API_REPO  = f"https://api.github.com/repos/{OWNER}/{REPO}"
API_TREE  = API_REPO + "/git/trees/{branch}?recursive=1"
API_BLOB  = API_REPO + "/git/blobs/{sha}"
OUT_PATH  = Path("stc_swc/normalize/swc_registry_full.json")

def session():
    s = requests.Session()
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        s.headers["Authorization"] = f"Bearer {tok}"
    s.headers["User-Agent"] = "stc-swc-fetcher"
    s.headers["Accept"] = "application/vnd.github+json"
    return s

def get_default_branch(s):
    r = s.get(API_REPO, timeout=30)
    r.raise_for_status()
    return r.json().get("default_branch", "master")

def get_tree(s, branch):
    r = s.get(API_TREE.format(branch=branch), timeout=60)
    r.raise_for_status()
    return r.json().get("tree", [])

def get_blob_text(s, sha):
    r = s.get(API_BLOB.format(sha=sha), timeout=30)
    r.raise_for_status()
    js = r.json()
    if js.get("encoding") == "base64":
        return base64.b64decode(js["content"]).decode("utf-8", "replace")
    return js.get("content", "")

def parse_md(md: str) -> dict:
    # Title
    m = re.search(r"^#\s*(.+)$", md, flags=re.MULTILINE)
    title = ""
    if m:
        title = m.group(1).strip()
        title = re.sub(r"^SWC-\d+\s*[-–—]\s*", "", title).strip()

    # Severity
    m = re.search(r"(?i)^\**\s*Severity\s*:\s*([A-Za-z]+)\s*$", md, flags=re.MULTILINE)
    severity = m.group(1).strip().lower() if m else ""

    # Remediation/Mitigation section
    remediation = ""
    sec = None
    for header in [r"(?i)^##\s*Remediation\s*$", r"(?i)^##\s*Mitigation\s*$"]:
        m = re.search(header, md, flags=re.MULTILINE)
        if m:
            start = m.end()
            m2 = re.search(r"(?m)^##\s+", md[start:])
            sec = md[start:] if not m2 else md[start:start+m2.start()]
            break
    if sec:
        lines = [ln.strip() for ln in sec.strip().splitlines() if ln.strip()]
        remediation = " ".join(lines)

    return {
        "title": title or None,
        "severity": severity or None,
        "remediation": remediation or None,
    }

def fetch_all():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    s = session()

    # 1) default branch
    branch = get_default_branch(s)
    print(f"[info] default_branch: {branch}", file=sys.stderr)

    # 2) list all files via tree
    tree = get_tree(s, branch)
    # ambil semua README.md di entries/SWC-xxx/
    targets = [t for t in tree
               if t.get("type") == "blob"
               and re.match(r"^entries/SWC-\d{3}/README\.md$", t.get("path",""))]

    print(f"[info] found {len(targets)} README.md entries", file=sys.stderr)

    entries = {}
    for i, t in enumerate(targets, 1):
        path = t["path"]  # entries/SWC-103/README.md
        m = re.search(r"SWC-(\d{3})", path)
        if not m:
            continue
        swc_num = m.group(1)

        # 3) ambil konten blob
        try:
            md = get_blob_text(s, t["sha"])
        except Exception as e:
            print(f"[warn] blob fetch failed {path}: {e}", file=sys.stderr)
            continue

        meta = parse_md(md)
        entries[swc_num] = {
            "id": swc_num,
            "title": meta["title"],
            "severity": meta["severity"],
            "description": None,
            "remediation": meta["remediation"],
            "relationships": None,
            "cwe": None,
            "references": None,
        }

        if i % 20 == 0:
            print(f"[info] processed {i}/{len(targets)}", file=sys.stderr)

    OUT_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ wrote {OUT_PATH} with {len(entries)} entries")

if __name__ == "__main__":
    fetch_all()
