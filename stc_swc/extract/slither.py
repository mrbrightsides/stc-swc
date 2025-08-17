import json
from pathlib import Path

def parse_report(path: str):
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    detectors = data.get("results", {}).get("detectors", [])
    findings = []

    for d in detectors:
        title = d.get("check") or d.get("title") or ""
        desc = d.get("description") or ""
        impact = (d.get("impact") or "").lower()
        conf = d.get("confidence", "").lower()
        conf_map = {"high": 0.9, "medium": 0.5, "low": 0.2}
        confidence = conf_map.get(conf, 0.5)

        file_path = ""
        line_start = 0
        line_end = 0
        contract = ""
        func = ""

        elements = d.get("elements", [])
        if elements:
            sm = elements[0].get("source_mapping", {})
            file_path = sm.get("filename_short") or sm.get("filename_relative") or ""

            lines = sm.get("lines", [])
            if isinstance(lines, list) and lines:
                line_start = min(lines)
                line_end = max(lines)

            parent = elements[0].get("type_specific_fields", {}).get("parent", {})
            contract = parent.get("name", "")
            func = elements[0].get("name", "") or ""

        findings.append({
            "swc_id": None,  # akan diisi belakangan via mapping
            "title": title,
            "description": desc,
            "severity": impact,
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
