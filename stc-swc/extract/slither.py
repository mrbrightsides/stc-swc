import json
from pathlib import Path

def parse_report(path: str):
    """
    Baca JSON hasil Slither (format --json) dan kembalikan list temuan raw standar internal.
    """
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    results = data.get("results", {})
    detectors = results.get("detectors", [])
    findings = []

    for d in detectors:
        title = d.get("check") or d.get("title") or ""
        desc = d.get("description") or ""
        impact = (d.get("impact") or "").lower()  # severity
        elements = d.get("elements", [])

        file_path = None
        line_no = None
        contract = ""
        func = ""

        for el in elements:
            sm = el.get("source_mapping") or {}
            file_path = sm.get("filename_absolute") or sm.get("filename_relative") or file_path
            line_no = sm.get("line") or line_no
            # Slither kadang punya tipe & function name
            if el.get("type") == "function":
                func = el.get("name") or func

        # Slither tidak menyediakan SWC-ID langsung → biarkan None (akan di-enrich nanti jika perlu)
        findings.append({
            "swc_id": None,
            "title": title,
            "description": desc,
            "severity": impact,
            "contract": contract,
            "function": func,
            "file": file_path,
            "line": int(line_no) if isinstance(line_no, int) or (isinstance(line_no, str) and str(line_no).isdigit()) else None,
        })

    return findings
