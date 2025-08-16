# tools_scan.py  — SWC standardizer
import json, os, hashlib, subprocess, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import pandas as pd

SEV_MAP = {
    "crit": "critical", "critical": "critical",
    "high": "high",
    "med": "medium", "medium": "medium",
    "low": "low", "info": "low", "informational": "low",
}

def now_utc_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()  # 2025-08-16T08:53:31

def get_commit_hash(cli_hash: Optional[str] = None) -> str:
    if cli_hash:
        return cli_hash
    try:
        h = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                    stderr=subprocess.DEVNULL).decode().strip()
        return h
    except Exception:
        return ""

def norm_severity(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = str(s).strip().lower()
    return SEV_MAP.get(s, s if s in {"critical","high","medium","low"} else None)

def coerce_int(x) -> Optional[int]:
    try:
        if x in ("", None): return None
        v = int(float(x))
        return v
    except Exception:
        return None

def coerce_float(x) -> Optional[float]:
    try:
        if x in ("", None): return None
        return float(x)
    except Exception:
        return None

def fallback_finding_id(contract: str, swc_id: str, line_start: Optional[int]) -> str:
    return f"{contract}::{swc_id}::{line_start or 0}"

def load_kb(kb_path: str = "swc_kb.json") -> Dict[str, Dict[str, Any]]:
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # normalisasikan key: "SWC-107" atau "107" -> "107"
        out = {}
        for k, v in data.items():
            key = str(k).replace("SWC-", "").strip()
            out[key] = v
        return out
    except Exception:
        return {}

# -----------------------------
# Parsers untuk berbagai tool
# -----------------------------

def parse_slither(slither_json: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Keluarkan dict minimal: swc_id, title, severity, confidence, file, line_start, line_end."""
    # Slither JSON shape bisa bervariasi; kita ambil path aman
    for f in slither_json.get("results", {}).get("detectors", []):
        swc_id = str(f.get("check", "")).replace("SWC-", "").strip()
        sev = f.get("impact") or f.get("severity")
        title = f.get("description") or f.get("check") or f.get("name") or ""
        conf = f.get("confidence")  # kadang tidak ada
        # ambil lokasi pertama yang ada
        file_path, lstart, lend = None, None, None
        if f.get("elements"):
            e0 = f["elements"][0]
            file_path = e0.get("source_mapping", {}).get("filename_absolute") or e0.get("source_mapping", {}).get("filename_relative")
            lstart = e0.get("source_mapping", {}).get("lines", [None])[0]
            lend   = e0.get("source_mapping", {}).get("lines", [None])[-1]
        yield {
            "swc_id": swc_id or None,
            "title": title.strip(),
            "severity": sev,
            "confidence": conf,
            "file": file_path,
            "line_start": lstart,
            "line_end": lend,
        }

def parse_mythril(myth_json: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for issue in myth_json.get("issues", []):
        swc_id = str(issue.get("swc-id", "")).replace("SWC-", "").strip()
        title  = issue.get("title") or issue.get("description") or ""
        sev    = issue.get("severity")
        conf   = issue.get("confidence")
        locs   = issue.get("locations", []) or issue.get("extra", {}).get("locations", [])
        file_path, lstart, lend = None, None, None
        if locs:
            srcmap = (locs[0].get("sourceMap") or {}).get("filename") or locs[0].get("sourceMap")
            file_path = locs[0].get("filename") or srcmap
            lstart = locs[0].get("line") or None
            lend   = locs[0].get("line_end") or lstart
        yield {
            "swc_id": swc_id or None,
            "title": title.strip(),
            "severity": sev,
            "confidence": conf,
            "file": file_path,
            "line_start": lstart,
            "line_end": lend,
        }

# -----------------------------
# Standardizer
# -----------------------------

def to_standard_df(records: Iterable[Dict[str, Any]],
                   network: str,
                   contract: str,
                   commit_hash: Optional[str],
                   kb_path: str = "swc_kb.json") -> pd.DataFrame:
    kb = load_kb(kb_path)
    ts = now_utc_iso()
    rows = []
    for r in records:
        swc_id = (str(r.get("swc_id", "")).replace("SWC-", "").strip()) or None
        severity = norm_severity(r.get("severity"))
        confidence = coerce_float(r.get("confidence"))
        file_rel = r.get("file") or ""
        rows.append({
            "finding_id": "",
            "timestamp": ts,
            "network": str(network or "").lower(),
            "contract": contract or "",
            "file": file_rel,
            "line_start": coerce_int(r.get("line_start")),
            "line_end":   coerce_int(r.get("line_end")),
            "swc_id": swc_id,
            "title": (r.get("title") or (f"SWC-{swc_id} finding" if swc_id else "SWC finding")).strip(),
            "severity": severity,
            "confidence": confidence,
            "status": "unresolved",
            "remediation": None,  # isi dari KB di bawah
            "commit_hash": get_commit_hash(commit_hash),
        })
    df = pd.DataFrame(rows)

    # finding_id fallback
    df["finding_id"] = df.apply(lambda x: fallback_finding_id(x["contract"], x["swc_id"] or "", x["line_start"])
                                if not x.get("finding_id") else x["finding_id"], axis=1)

    # remediation dari KB jika ada
    if not df.empty:
        def kb_text(x):
            k = (x or "").replace("SWC-", "")
            info = kb.get(k or "", {})
            return info.get("remediation") or info.get("explanation") or None
        df["remediation"] = df["swc_id"].map(kb_text)

    # tipe kolom bersih
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["severity"]  = df["severity"].astype("string")
    df["title"]     = df["title"].astype("string")
    df["status"]    = df["status"].astype("string")
    for c in ["finding_id","network","contract","file","swc_id","remediation","commit_hash"]:
        df[c] = df[c].fillna("").astype("string")
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    df["line_start"] = pd.to_numeric(df["line_start"], errors="coerce").astype("Int64")
    df["line_end"]   = pd.to_numeric(df["line_end"],   errors="coerce").astype("Int64")

    # urutan final
    cols = ["finding_id","timestamp","network","contract","file",
            "line_start","line_end","swc_id","title","severity",
            "confidence","status","remediation","commit_hash"]
    return df[cols]
