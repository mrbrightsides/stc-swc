import json
from pathlib import Path

def parse_report(path: str):
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    issues = data.get("issues", [])
    findings = []

    for it in issues:
        swc_id = it.get("swc-id") or it.get("swcID") or it.get("swcid")
        title = it.get("title") or ""
        desc = it.get("description") or ""
        severity = (it.get("severity") or "").lower()

        conf_map = {"high": 0.9, "medium": 0.5, "low": 0.2}
        confidence = conf_map.get(severity, 0.5)

        # Lokasi
        file_path = ""
        line_start = 0
        line_end = 0
        contract = ""
        func = ""

        locs = it.get("locations") or it.get("location") or []
        if isinstance(locs, dict):
            locs = [locs]

        if locs:
            loc = locs[0]
            file_path = loc.get("file", "")
            line = loc.get("line", 0)
            if isinstance(line, int):
                line_start = line_end = line

        meta = it.get("extra") or {}
        contract = meta.get("contract") or ""
        func = meta.get("function") or ""

        findings.append({
            "swc_id": swc_id,
            "title": title,
            "description": desc,
            "severity": severity,
            "confidence": confidence,
            "status": "unresolved",
            "contract": contract,
            "function": func,
            "file": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "remediation": "",
            "commit_hash": "",
            "network": "ethereum",
        })

    return findings
