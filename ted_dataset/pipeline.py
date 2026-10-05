"""CLI: fetch a snapshot, process offline, update evidence reports."""
import argparse
import json
import shutil
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from .common import digest, read_json, safe_path, write_json
from .evidence import ROOT, test_evidence, processing_digest
from .export import COLUMNS, REJECT_COLUMNS, export_workbook, write_csv, read_csv, csv_value
from .fetch import fetch_snapshot, load_snapshot
from .qa import make_sample, review_sample, CHECKS, REVIEW_FIELDS
from .reference import load_reference
from .report import render_report
from .validate import process_records


def process_snapshot(run, output, reference=ROOT/"data/reference", target=300):
    run, output, reference = Path(run), Path(output), Path(reference)
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}. Choose a new output directory.")
    manifest, records = load_snapshot(run)
    # Preserve exact reference versions with the run before producing any output.
    if not (run / "reference").exists():
        load_reference(reference)
        shutil.copytree(reference, run / "reference")
    refs = load_reference(run / "reference")
    result = process_records(records, refs, date.fromisoformat(manifest["date_start"]),
                             date.fromisoformat(manifest["as_of"]), target)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "delivery_manifest.json", {"status": "incomplete"})
    (output / "qa").mkdir()
    write_csv(output/"validated_notices.csv", COLUMNS, result.selected)
    write_csv(output/"valid_not_selected.csv", COLUMNS, result.not_selected)
    write_csv(output/"rejected_or_uncertain.csv", REJECT_COLUMNS, result.rejected)
    write_csv(output/"record_ledger.csv", ["raw_ref", "notice_id", "disposition", "reason_code"], result.ledger)
    snapshot_id = digest((run/"ted_raw.json").read_bytes())
    dataset_hash = digest((output/"validated_notices.csv").read_bytes())
    raw_refs = {e["notice_id"]: e["raw_ref"] for e in result.ledger if e["disposition"] == "selected"}
    sample = make_sample(result.selected, snapshot_id, dataset_hash, raw_refs)
    write_json(output/"qa/expected_sample.json", sample)
    sample_columns = list(sample[0]) if sample else (["snapshot_id", "dataset_sha256", "notice_id", "source_url", "raw_ref"] +
                     ["expected_"+f for fields in CHECKS.values() for f in fields] + ["expected_qa_note"] + REVIEW_FIELDS)
    write_csv(output/"qa/manual_qa_sample.csv", sample_columns, sample)
    serial_rows = [{k: csv_value(v) if isinstance(v, Decimal) else v for k, v in row.items()} for row in result.selected]
    stored = dict(snapshot_id=snapshot_id, reference_id=refs.identity, selected=serial_rows,
                  rejected=result.rejected, metrics=result.metrics)
    write_json(output/"result.json", stored)
    files = ["validated_notices.csv", "valid_not_selected.csv", "rejected_or_uncertain.csv", "record_ledger.csv",
             "result.json", "qa/expected_sample.json"]
    hashes = {name: digest((output/name).read_bytes()) for name in files}
    delivery = dict(status="complete", snapshot_id=snapshot_id, reference_id=refs.identity, files=hashes,
                    processing_code_sha256=processing_digest())
    write_json(output/"delivery_manifest.json", delivery)
    try:
        update_report(run, output)
    except BaseException:
        delivery["status"] = "incomplete"
        write_json(output/"delivery_manifest.json", delivery)
        raise
    return output


def update_report(run, output, evidence=None):
    run, output = Path(run), Path(output)
    manifest, _ = load_snapshot(run)
    delivery = read_json(output/"delivery_manifest.json")
    if delivery.get("status") != "complete":
        raise ValueError("Delivery incomplete")
    if delivery.get("processing_code_sha256") != processing_digest():
        raise ValueError("Processing code changed: reprocess snapshot into a new output directory")
    if digest((run/"ted_raw.json").read_bytes()) != delivery["snapshot_id"]:
        raise ValueError("Snapshot identity mismatch")
    if load_reference(run/"reference").identity != delivery["reference_id"]:
        raise ValueError("Reference identity mismatch")
    for name, checksum in delivery["files"].items():
        if digest(safe_path(output, name).read_bytes()) != checksum:
            raise ValueError(f"Delivery checksum mismatch: {name}")
    stored = read_json(output/"result.json")
    expected = read_json(output/"qa/expected_sample.json")
    manual = review_sample(read_csv(output/"qa/manual_qa_sample.csv"), expected)
    automated = test_evidence(evidence)
    export_workbook(output/"validated_notices.xlsx", stored["selected"], stored["rejected"],
                    stored["metrics"], manual, automated)
    (output/"QA_REPORT.md").write_text(render_report(manifest, stored, manual, automated), encoding="utf-8")
    write_json(output/"report_status.json", {"manual": manual, "automated": automated,
                                            "publication_ready": manual["status"] == automated["status"] == "passed"})
    return manual


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="Read public TED API into a new immutable snapshot")
    fetch.add_argument("--as-of", type=date.fromisoformat, default=datetime.now(ZoneInfo("Europe/Minsk")).date())
    fetch.add_argument("--run", type=Path)
    process = commands.add_parser("process", help="Offline processing; refuses existing outputs")
    process.add_argument("--run", type=Path, required=True)
    process.add_argument("--output", type=Path)
    process.add_argument("--reference", type=Path, default=ROOT/"data/reference")
    process.add_argument("--target", type=int, default=300)
    report = commands.add_parser("report", help="Validate human QA and update report/XLSX summary")
    report.add_argument("--run", type=Path, required=True)
    report.add_argument("--output", type=Path)
    report.add_argument("--evidence", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "fetch":
            run = args.run or ROOT/"data/runs"/f"{args.as_of}-{uuid4().hex[:8]}"
            print(fetch_snapshot(run, args.as_of))
        elif args.command == "process":
            print(process_snapshot(args.run, args.output or args.run/"processed", args.reference, args.target))
        else:
            print(json.dumps(update_report(args.run, args.output or args.run/"processed", args.evidence), indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
