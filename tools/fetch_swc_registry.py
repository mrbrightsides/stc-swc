#!/usr/bin/env python3
"""
Robust SWC registry fetcher.

- Coba tarik JSON per entry (jika ada).
- Kalau 404, fallback tarik README.md dan parsing Title/Severity/Remediation.
- Simpan cache ke: stc_swc/normalize/swc_registry_full.json

Dependensi: requests
"""
from pathlib import Path
import os, json, re, requests, sys

OWNER = "SmartContractSecurity"
REPO  = "SWC-registry"
BRANCHES = ["master", "main"]          # urutan coba
ID_RANGE = range(100, 201)             # perluas kalau mau (mis. 100..300)

OUT_PATH = Path("stc_swc/normalize/swc_registry_full.json")

def _session():
    s = requests.Session()
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        s.headers["Authorization"] = f"Bearer {tok}"
    s.headers["User-Agent"] = "stc-swc-fetcher"
    return s

def _fetch_raw(s, url: str) -> str | None:
    try:
        r = s.get(url, timeout=25)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print(f"[warn] fetch failed: {url} ({e})", file=sys.stderr)
    return None

def _parse_md(md: str) -> dict:
    """
    Parsers very simple SWC README.md structure.

    Heuristics:
      - Title: first H1 or first line containing 'SWC-xxx — Title'
      - Severity: line with 'Severity:' (case-insensitive)
      - Remediation/Mitigation: section content under '## Remediation' or '## Mitigation'
    """
    title = ""
    severity = ""
    remediation = ""

    # Title: first H1
    m = re.search(r"^#\s*(.+)$", md, flags=re.MULTILINE)
    if m:
        # often like: "SWC-103 — Floating Pragma"
        title = m.group(1).strip()
        # normalize: drop "SWC-xxx — "
        title = re.sub(r"^SWC-\d+\s*[-–—]\s*", "", title).strip()

    # Severity: "**Severity:** Medium" or "Severity: Medium"
    m = re.search(r"(?i)^\**\s*Severity\s*:\s*([A-Za-z]+)\s*$", md, flags=re.MULTILINE)
    if m:
        severity = m.group(1).strip().lower()

    # Remediation/Mitigation section: from header to next '##'
    sec = None
    for header in [r"(?i)^##\s*Remediation\s*$", r"(?i)^##\s*Mitigation\s*$"]:
        m = re.search(header, md, flags=re.MULTILINE)
        if m:
            start = m.end()
            m2 = re.search(r"(?m)^##\s+", md[start:])  # next section
            sec = md[start:] if not m2 else md[start:start+m2.start()]
            break
    if sec:
        # compress whitespace; keep bullets
        lines = [ln.strip() for ln in sec.strip().splitlines() if ln.strip()]
        remediation = " ".join(lines)

    return {
        "title": title or None,
        "severity": severity or None,
        "remediation": remediation or None,
    }

def fetch_all():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    s = _session()
    entries = {}
    fetched = 0

    for swc_id in ID_RANGE:
        name = f"SWC-{swc_id}"
        data = None

        # 1) coba JSON (kalau suatu saat tersedia)
        for br in BRANCHES:
            url_json = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{br}/entries/{name}/{name}.json"
            txt = _fetch_raw(s, url_json)
            if txt:
                try:
                    jj = json.loads(txt)
                    data = {
                        "id": str(jj.get("SWC-ID") or swc_id),
                        "title": jj.get("Title"),
                        "severity": (jj.get("Severity") or "").lower() or None,
                        "description": jj.get("Description"),
                        "remediation": jj.get("Remediation") or jj.get("Mitigation"),
                        "relationships": jj.get("Relationships"),
                        "cwe": jj.get("CWE"),
                        "references": jj.get("References"),
                    }
                    break
                except Exception:
                    pass  # lanjut fallback ke README.md

        # 2) fallback ke README.md
        if not data:
            md = None
            for br in BRANCHES:
                url_md = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{br}/entries/{name}/README.md"
                md = _fetch_raw(s, url_md)
                if md:
                    break
            if not md:
                continue  # entry tidak ada → lanjut

            meta = _parse_md(md)
            data = {
                "id": str(swc_id),
                "title": meta["title"],
                "severity": meta["severity"],
                "description": None,
                "remediation": meta["remediation"],
                "relationships": None,
                "cwe": None,
                "references": None,
            }

        key = str(data["id"]).replace("SWC-", "")
        entries[key] = data
        fetched += 1
        if fetched % 10 == 0:
            print(f"[info] fetched {fetched} entries...", file=sys.stderr)

    OUT_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ wrote {OUT_PATH} with {len(entries)} entries")

if __name__ == "__main__":
    fetch_all()
