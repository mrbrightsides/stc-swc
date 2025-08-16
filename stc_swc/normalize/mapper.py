from datetime import datetime, timezone
from .swc_registry import get_swc_meta
import json
from uuid import uuid4

def _norm_severity(x: str) -> str:
    if not x:
        return "medium"
    x = x.strip().lower()
    if x in {"low","medium","high","critical"}:
        return x
    # mapping long forms
    if x in {"informational","info"}: return "low"
    if x in {"severe","very high"}: return "critical"
    return x or "medium"

def to_stc_schema(raw: dict, tool: str, timestamp_iso: str | None = None) -> dict:
    swc_id = raw.get("swc_id")
    title = raw.get("title") or ""
    description = raw.get("description") or ""
    severity = _norm_severity(raw.get("severity"))

    # Enrich dari registry jika ada swc_id
    meta = get_swc_meta(swc_id) if swc_id else None
    if meta:
        # gunakan title SWC resmi bila title kosong/umum
        if not title or len(title) < 3:
            title = meta.get("title", title)
        # jika severity kosong, pakai default dari registry
        if not raw.get("severity"):
            severity = _norm_severity(meta.get("severity"))

    meta = get_swc_meta(raw.get("swc_id"))
    if meta:
        raw["title"]       = raw.get("title")       or meta.get("title")
        raw["severity"]    = raw.get("severity")    or (meta.get("severity") or "").lower()
        raw["remediation"] = raw.get("remediation") or meta.get("remediation") or ""

    ts = timestamp_iso
    if not ts:
        ts = datetime.now(timezone.utc).isoformat()

    return {
        "finding_id": str(uuid4()),
        "timestamp": ts,
        "network": "ethereum",
        "contract": raw.get("contract") or "",
        "file": raw.get("file") or "",
        "line_start": int(raw.get("line")) if raw.get("line") not in (None, "") else 0,
        "line_end": int(raw.get("line")) if raw.get("line") not in (None, "") else 0,
        "swc_id": swc_id or "",
        "title": title[:200],
        "severity": severity,
        "confidence": "medium",
        "status": "unresolved",
        "remediation": "",
        "commit_hash": "",
    }

def to_stc_schema_batch(raw_list: list[dict], tool: str, timestamp_iso: str | None = None) -> list[dict]:
    rows = []
    for r in raw_list:
        rows.append(to_stc_schema(r, tool=tool, timestamp_iso=timestamp_iso))
    return rows
