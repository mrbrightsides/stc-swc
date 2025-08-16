from __future__ import annotations
from uuid import uuid4
from datetime import datetime

from stc_swc.normalize.swc_registry import get_swc_meta

_SEV_MAP = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}

def _norm_severity(s: str | None) -> str:
    if not s:
        return ""
    s = str(s).strip().lower()
    return _SEV_MAP.get(s, s)

def to_stc_schema(raw: dict, tool: str, timestamp_iso: str | None = None) -> dict:
    # ambil nilai awal dari parser
    swc_id      = (raw.get("swc_id") or "").strip()
    title       = (raw.get("title") or "").strip()
    severity    = _norm_severity(raw.get("severity"))
    remediation = (raw.get("remediation") or "").strip()

    # enrich dari registry kalau ada SWC-ID
    if swc_id:
        meta = get_swc_meta(swc_id) or get_swc_meta(swc_id.replace("SWC-", ""))
        if meta:
            if not title:
                title = (meta.get("title") or "").strip()
            if not severity:
                severity = _norm_severity(meta.get("severity"))
            if not remediation:
                remediation = (meta.get("remediation") or "").strip()

    # timestamp & line fallback
    ts = timestamp_iso or datetime.utcnow().isoformat(timespec="seconds")
    line_start = raw.get("line_start") or raw.get("line") or 0
    line_end   = raw.get("line_end") or line_start

    def _to_int(x):
        try:
            return int(x)
        except Exception:
            return 0

    return {
        "finding_id": str(uuid4()),
        "timestamp": ts,
        "network":   raw.get("network") or "ethereum",
        "contract":  raw.get("contract") or "",
        "file":      raw.get("file") or "",
        "line_start": _to_int(line_start),
        "line_end":   _to_int(line_end),
        "swc_id":     swc_id,
        "title":      title,          # <- hasil enrich
        "severity":   severity,       # <- hasil enrich
        "confidence": raw.get("confidence") or "medium",
        "status":     raw.get("status") or "unresolved",
        "remediation": remediation,   # <- hasil enrich
        "commit_hash": raw.get("commit_hash") or "",
    }

def to_stc_schema_batch(raw_list: list[dict], tool: str, timestamp_iso: str | None = None) -> list[dict]:
    return [to_stc_schema(r, tool=tool, timestamp_iso=timestamp_iso) for r in raw_list]
