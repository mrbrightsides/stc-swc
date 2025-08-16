from stc_swc.normalize.swc_registry import get_swc_meta

def to_stc_schema(raw: dict, tool: str, timestamp_iso: str | None = None) -> dict:
    # ambil nilai awal
    title       = (raw.get("title") or "").strip()
    severity    = (raw.get("severity") or "").strip().lower()
    remediation = (raw.get("remediation") or "").strip()

    # kalau ada SWC-ID, ambil meta dari registry
    swc_id = raw.get("swc_id")
    meta = get_swc_meta(swc_id) if swc_id else None
    if meta:
        if not title:
            title = (meta.get("title") or "").strip()
        if not severity:
            severity = (meta.get("severity") or "").strip().lower()
        if not remediation:
            remediation = (meta.get("remediation") or "").strip()

    # normalisasi severity jika perlu
    sev_map = {"critical":"critical","high":"high","medium":"medium","low":"low"}
    severity = sev_map.get(severity, severity or "")

    # timestamp
    ts = timestamp_iso or datetime.utcnow().isoformat(timespec="seconds")

    # line_end fallback
    line_start = raw.get("line_start") or raw.get("line")
    line_end   = raw.get("line_end") or line_start

    return {
        "finding_id": str(uuid4()),
        "timestamp": ts,
        "network": (raw.get("network") or "ethereum"),
        "contract": (raw.get("contract") or ""),
        "file":     (raw.get("file") or ""),
        "line_start": int(line_start) if str(line_start).isdigit() else 0,
        "line_end":   int(line_end)   if str(line_end).isdigit()   else 0,
        "swc_id": swc_id or "",
        "title": title,                # <- pakai variabel hasil enrich
        "severity": severity,          # <-
        "confidence": (raw.get("confidence") or "medium"),
        "status": (raw.get("status") or "unresolved"),
        "remediation": remediation,    # <-
        "commit_hash": (raw.get("commit_hash") or "")
    }
