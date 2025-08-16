#!/usr/bin/env python3
"""
SWC Registry fetcher via GitHub Commits + Tree + Blob API (robust).

- GET /repos/{owner}/{repo}/commits/{branch}  -> ambil tree.sha
- GET /repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1
- Filter path: entries/SWC-xxx/README.md
- GET /repos/{owner}/{repo}/git/blobs/{sha}   -> base64 decode
- Parse Markdown -> title, severity, remediation
- Tulis cache ke stc_swc/normalize/swc_registry_full.json

Set env opsional:
  GITHUB_TOKEN  (biar rate limit longgar)
"""
from pathlib import Path
import os, re, json, base64, requests, sys

OWNER = "SmartContractSecurity"
REPO  = "SWC-registry"
API_BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"

OUT_PATH = Path("stc_swc/normalize/swc_registry_full.json")

def sess():
    s = requests.Session()
    if os.getenv("GITHUB_TOKEN"):
        s.headers["Authorization"] = f"Bearer {os.getenv('GITHUB_TOKEN')}"
    s.headers["User-Agent"] = "stc-swc-fetcher"
    s.headers["Accept"] = "application/vnd.github+json"
    return s

def get_default_branch(s):
    r = s.get(API_BASE, timeout=30); r.raise_for_status()
    return r.json().get("default_branch", "master")

def get_tree_sha(s, branch):
    # commits/{branch} -> commit.tree.sha
    r = s.get(f"{API_BASE}/commits/{branch}", timeout=30); r.raise_for_status()
    js = r.json()
    tree = js.get("commit", {}).get("tree", {})
    sha = tree.get("sha")
    if not sha:
        raise RuntimeError("tree sha not found")
    return sha

def get_tree_recursive(s, tree_sha):
    r = s.get(f"{API_BASE}/git/trees/{tree_sha}?recursive=1", timeout=60)
    r.raise_for_status()
    return r.json().get("tree", [])

def get_blob_text(s, blob_sha):
    r = s.get(f"{API_BASE}/git/blobs/{blob_sha}", timeout=30); r.raise_for_status()
    js = r.json()
    if js.get("encoding") == "base64":
        return base64.b64decode(js["content"]).decode("utf-8", "replace")
    return js.get("content", "")

def parse_md(md: str) -> dict:
    # Title = first H1 (drop "SWC-xxx — ")
    m = re.search(r"^#\s*(.+)$", md, flags=re.MULTILINE)
    title = (m.group(1).strip() if m else "")
    title = re.sub(r"^SWC-\d+\s*[-–—]\s*", "", title).strip()

    # Severity: line with "Severity: X"
    m = re.search(r"(?i)^\**\s*Severity\s*:\s*([A-Za-z]+)\s*$", md, flags=re.MULTILINE)
    severity = (m.group(1).strip().lower() if m else "")

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

    return {"title": title or None, "severity": severity or None, "remediation": remediation or None}

def fetch_all():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    s = sess()

    branch = get_default_branch(s)
    print(f"[info] default_branch: {branch}", file=sys.stderr)

    tree_sha = get_tree_sha(s, branch)
    print(f"[info] tree_sha: {tree_sha}", file=sys.stderr)

    tree = get_tree_recursive(s, tree_sha)
    targets = [t for t in tree
               if t.get("type") == "blob"
               and re.match(r"^entries/SWC-\d{3}/README\.md$", t.get("path",""))]

    print(f"[info] found {len(targets)} README.md entries", file=sys.stderr)

    entries = {}
    for i, t in enumerate(targets, 1):
        path = t["path"]                                  # entries/SWC-103/README.md
        m = re.search(r"SWC-(\d{3})", path)
        if not m: continue
        swc_num = m.group(1)

        md = get_blob_text(s, t["sha"])
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
