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

    if tool == "mythril":
        raw_findings = parse_mythril(str(tmp_path))
    else:
        raw_findings = parse_slither(str(tmp_path))

    rows = to_stc_schema_batch(raw_findings, tool=tool, timestamp_iso=timestamp_now or None)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    csv_path = out_dir / f"swc_findings_{ts}.csv"
    ndj_path = out_dir / f"swc_findings_{ts}.ndjson"

    write_csv(rows, str(csv_path))
    write_ndjson(rows, str(ndj_path))

    st.success("Berhasil diexport!")

    with open(csv_path, "rb") as f:
        st.download_button("📥 Download CSV", f, file_name=csv_path.name, mime="text/csv")

    with open(ndj_path, "rb") as f:
        st.download_button("📥 Download NDJSON", f, file_name=ndj_path.name, mime="application/x-ndjson")

    if rows:
        st.dataframe(pd.DataFrame(rows))
