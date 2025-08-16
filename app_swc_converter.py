import json
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st

# --- bootstrap local package path (supports running from subfolders like main/) ---
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE if (HERE / "stc_swc").exists() else HERE.parent
for p in {str(ROOT), str(ROOT / "stc_swc")}:
    if p not in sys.path:
        sys.path.insert(0, p)
# -------------------------------------------------------------------------------

from stc_swc.extract.mythril import parse_report as parse_mythril
from stc_swc.extract.slither import parse_report as parse_slither
from stc_swc.normalize.mapper import to_stc_schema_batch
from stc_swc.export.csv_exporter import write_csv
from stc_swc.export.ndjson_exporter import write_ndjson
from stc_swc.normalize.swc_registry import get_swc_meta

st.set_page_config(page_title="STC for SWC — Converter", layout="wide")
st.title("🛡️ STC for SWC — Converter")

st.markdown(
    "Konversi output **Mythril/Slither (JSON)** menjadi **swc_findings.csv** & **swc_findings.ndjson** yang selaras STC Analytics."
)

col = st.columns([1, 1])  # hanya 2 kolom sekarang
with col[0]:
    tool = st.selectbox("Pilih tool", ["mythril", "slither"], index=0)
with col[1]:
    timestamp_now = st.text_input("Timestamp (opsional, ISO)", "", placeholder="2025-08-10T13:00:00")

out_dir = Path("outputs")
out_dir.mkdir(parents=True, exist_ok=True)

report_file = st.file_uploader("Upload output JSON (Mythril/Slither)", type=["json"], accept_multiple_files=False)

if st.session_state.get("converted"):
    st.success("Berhasil diexport!")

    csv_path = Path(st.session_state["csv_path"])
    ndj_path = Path(st.session_state["ndj_path"])
    rows = st.session_state["rows"]

    with open(csv_path, "rb") as f:
        st.download_button("📥 Download CSV", f, file_name=csv_path.name, mime="text/csv", key="csv_dl")

    with open(ndj_path, "rb") as f:
        st.download_button("📥 Download NDJSON", f, file_name=ndj_path.name, mime="application/x-ndjson", key="ndjson_dl")

    st.dataframe(pd.DataFrame(rows))

if st.button("▶️ Konversi", use_container_width=True):
    if not report_file:
        st.error("Upload report JSON dulu ya.")
        st.stop()

    if timestamp_now:
        try:
            datetime.fromisoformat(timestamp_now)
        except ValueError:
            st.error("Format timestamp harus YYYY-MM-DDTHH:MM:SS")
            st.stop()

    tmp_path = out_dir / "_tmp_report.json"
    tmp_path.write_bytes(report_file.read())

    # --- ambil nama file utk default contract name
    contract_guess = Path(report_file.name).stem.split(".")[0]

    # --- ambil git commit hash otomatis
    def get_commit_hash():
        try:
            import subprocess
            return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
        except:
            return ""

    commit_hash = get_commit_hash()

    # --- parsing file JSON
    if tool == "mythril":
        raw_findings = parse_mythril(str(tmp_path))
    else:
        raw_findings = parse_slither(str(tmp_path))

    # --- isi metadata ke semua temuan
    for f in raw_findings:
        f["contract"] = f.get("contract") or contract_guess
        f["network"] = f.get("network") or "ethereum"
        f["commit_hash"] = f.get("commit_hash") or commit_hash
        f["timestamp"] = timestamp_now or datetime.utcnow().isoformat(timespec="seconds")
        if "status" not in f:
            f["status"] = "unresolved"
        if "confidence" not in f or f["confidence"] in (None, ""):
            f["confidence"] = "medium"

    # -------------------------------
    # Lengkapi metadata per temuan
    # -------------------------------
    
    # Ambil nama kontrak dari nama file (mis. SmartToken.slither.json → SmartToken)
    contract_guess = Path(report_file.name).stem.split(".")[0]
    
    # Ambil git commit hash (jika tersedia)
    def get_commit_hash():
        try:
            import subprocess
            return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
        except:
            return ""
    
    commit_hash = get_commit_hash()
    
    # SWC Mapping contoh minimal
    SWC_MAPPING = {
        "reentrancy": "SWC-107",
        "low-level-calls": "SWC-104",
        "solc-version": "SWC-103",
        # tambahkan sesuai tool
    }
    
    for f in raw_findings:
        f["contract"] = f.get("contract") or contract_guess
        f["network"] = f.get("network") or "ethereum"
        f["commit_hash"] = f.get("commit_hash") or commit_hash
        f["timestamp"] = f.get("timestamp") or timestamp_now or datetime.utcnow().isoformat(timespec="seconds")
    
        if not f.get("status"):
            f["status"] = "unresolved"
    
        if not f.get("confidence") or f["confidence"] in ("", None):
            f["confidence"] = 0.5  # default confidence
    
        if not f.get("line_start") and f.get("line"):
            f["line_start"] = f["line"]
        if not f.get("line_end"):
            f["line_end"] = f.get("line_start")
    
        # isi swc_id dari judul jika cocok
        title_lc = (f.get("title") or "").lower()
        for k, v in SWC_MAPPING.items():
            if k in title_lc:
                f["swc_id"] = v
                break

    # ------ Enrich dari registry & isi default ------
    for f in raw_findings:
        # metadata umum
        f["contract"]    = f.get("contract")    or Path(report_file.name).stem.split(".")[0]
        f["network"]     = f.get("network")     or "ethereum"
        f["commit_hash"] = f.get("commit_hash") or commit_hash
        f["timestamp"]   = f.get("timestamp")   or (timestamp_now or datetime.utcnow().isoformat(timespec="seconds"))
        f["status"]      = f.get("status")      or "unresolved"
        f["confidence"]  = f.get("confidence")  or "medium"
    
        # line_end fallback
        if not f.get("line_end") and f.get("line_start"):
            f["line_end"] = f["line_start"]
    
        # SWC-ID dari judul (fallback ringan)
        if not f.get("swc_id"):
            title_lc = (f.get("title") or "").lower()
            for k, v in {
                "reentrancy": "SWC-107",
                "low-level-calls": "SWC-104",
                "solc-version": "SWC-103",
                "tx-origin": "SWC-115",
                "unchecked-send": "SWC-113",
            }.items():
                if k in title_lc:
                    f["swc_id"] = v
                    break
    
        # Enrich dari SWC Registry
        meta = get_swc_meta(f.get("swc_id"))
        if meta:
            # Jangan override kalau scanner sudah kasih value
            f["title"]       = f.get("title")       or meta.get("title")
            f["severity"]    = f.get("severity")    or meta.get("severity")
            f["remediation"] = f.get("remediation") or meta.get("remediation") or ""


    # --- konversi ke schema final
    rows = to_stc_schema_batch(raw_findings, tool=tool)

    # --- simpan hasil ke file
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    csv_path = out_dir / f"swc_findings_{ts}.csv"
    ndj_path = out_dir / f"swc_findings_{ts}.ndjson"

    write_csv(rows, str(csv_path))
    write_ndjson(rows, str(ndj_path))

    st.session_state["converted"] = True
    st.session_state["csv_path"] = str(csv_path)
    st.session_state["ndj_path"] = str(ndj_path)
    st.session_state["rows"] = rows

    st.rerun()
