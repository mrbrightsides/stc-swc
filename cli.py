import argparse
from pathlib import Path
from stc_swc.extract.mythril import parse_report as parse_mythril
from stc_swc.extract.slither import parse_report as parse_slither
from stc_swc.normalize.mapper import to_stc_schema_batch
from stc_swc.export.csv_exporter import write_csv
from stc_swc.export.ndjson_exporter import write_ndjson

def main():
    ap = argparse.ArgumentParser(description="STC for SWC Converter (Mythril/Slither JSON → STC Analytics schema)")
    ap.add_argument("--tool", required=True, choices=["mythril", "slither"])
    ap.add_argument("--input", required=True, help="Path ke file JSON report")
    ap.add_argument("--out-dir", default="outputs")
    ap.add_argument("--timestamp", default="", help="Override timestamp ISO (opsional)")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.tool == "mythril":
        raw = parse_mythril(args.input)
    else:
        raw = parse_slither(args.input)

    rows = to_stc_schema_batch(raw, tool=args.tool, timestamp_iso=args.timestamp or None)

    csv_path = out_dir / "swc_findings.csv"
    ndj_path = out_dir / "swc_findings.ndjson"

    write_csv(rows, str(csv_path))
    write_ndjson(rows, str(ndj_path))

    print(f"OK → {csv_path}")
    print(f"OK → {ndj_path}")

if __name__ == "__main__":
    main()
