# STC for SWC (Smart Contract Weakness Classification)

Converter modular untuk mengubah hasil audit **Mythril** / **Slither** menjadi format standar **STC Analytics**:

- `swc_findings.csv`
- `swc_findings.ndjson`

## Quick Start

```bash
pip install -r requirements.txt

# jalankan Mythril/Slither sendiri dulu, simpan output JSON ke outputs/
# contoh:
# myth analyze examples/contracts/SimpleBank.sol -o json > outputs/mythril.json
# slither examples/contracts/SimpleBank.sol --json outputs/slither.json

# UI (Streamlit)
streamlit run app_swc_converter.py

# CLI
python -m stc_swc.cli --tool mythril --input outputs/mythril.json --out-dir outputs
