import json
from pathlib import Path

def parse_report(path: str):
    """
    Baca JSON hasil Mythril dan kembalikan list temuan dengan struktur raw standar internal.
    Output list of dict minimal fields:
      - swc_id (bisa None)
      - title
      - description
      - severity
      - contract
      - function
      - file
      - line (int/None)
    """
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    issues = data.get("issues", [])
    findings = []
    for it in issues:
        swc_id = it.get("swc-id") or it.get("swcID") or it.get("swcid")
        title = it.get("title") or ""
        desc = it.get("description") or ""
        severity = (it.get("severity") or "").lower()

        # Lokasi
        file_path = None
        line_no = None
        contract = ""
        func = ""
        locs = it.get("locations") or it.get("location") or []
        if isinstance(locs, dict):
            locs = [locs]
        for loc in locs:
            file_path = loc.get("file") or file_path
            line_no = loc.get("line") or line_no
            # Mythril kadang tidak mencantumkan function; biarkan kosong

        # Beberapa report menyimpan detail di extra fields
        meta = it.get("extra") or {}
        contract = meta.get("contract") or contract
        func = meta.get("function") or func

        findings.append({
            "swc_id": swc_id,
            "title": title,
            "description": desc,
            "severity": severity,
            "contract": contract,
            "function": func,
            "file": file_path,
            "line": int(line_no) if isinstance(line_no, int) or (isinstance(line_no, str) and line_no.isdigit()) else None,
        })

    return findings
