"""Human-review sampling. Never infer a human pass from automated checks."""
import random
from datetime import date

from .export import csv_value

CHECKS = {"title": ["title"], "buyer": ["buyer", "buyer_country"],
          "cpv": ["cpv_code", "cpv_description"], "publication_date": ["publication_date"],
          "deadline": ["deadline"], "value": ["estimated_value", "currency"]}
REVIEW_FIELDS = [k + "_match" for k in CHECKS] + ["review_status", "reviewed_by", "reviewed_at", "review_notes"]


def make_sample(selected, snapshot_id, dataset_sha256, raw_refs):
    ordered = sorted(selected, key=lambda row: row["notice_id"])
    chosen = random.Random(42).sample(ordered, min(20, len(ordered)))
    result = []
    for row in chosen:
        r = dict(snapshot_id=snapshot_id, dataset_sha256=dataset_sha256, notice_id=row["notice_id"],
                 source_url=row["source_url"], raw_ref=raw_refs.get(row["notice_id"], ""))
        for keys in CHECKS.values():
            r.update({"expected_" + k: csv_value(row[k]) for k in keys})
        r["expected_qa_note"] = row["qa_note"]
        r.update({k: "" for k in REVIEW_FIELDS})
        r["review_status"] = "pending"
        result.append(r)
    return result


def review_sample(supplied, expected):
    if len(supplied) != len(expected) or len({r["notice_id"] for r in supplied}) != len(supplied):
        raise ValueError("Manual QA membership mismatch")
    by_id = {r["notice_id"]: r for r in expected}
    completed = mismatches = 0
    for row in supplied:
        original = by_id.get(row["notice_id"])
        if original is None or any(row.get(k) != v for k, v in original.items() if k not in REVIEW_FIELDS):
            raise ValueError("Manual QA snapshot or expected values changed")
        if row["review_status"] not in {"pending", "reviewed"}:
            raise ValueError("review_status must be pending or reviewed")
        for key in CHECKS:
            if row.get(key + "_match", "") not in {"", "match", "mismatch", "not_applicable"}:
                raise ValueError("Invalid manual check value")
        mismatch = any(row.get(k + "_match") == "mismatch" for k in CHECKS)
        mismatches += mismatch
        if row["review_status"] == "reviewed":
            if not row["reviewed_by"].strip():
                raise ValueError("Reviewer is required")
            date.fromisoformat(row["reviewed_at"])
            for key, fields in CHECKS.items():
                value = row[key + "_match"]
                if not value:
                    raise ValueError("Reviewed row has unfinished checks")
                if value == "not_applicable" and any(original["expected_"+f] for f in fields):
                    raise ValueError("Cannot skip a populated field")
            completed += 1
    status = "mismatch" if mismatches else "passed" if expected and completed == len(expected) else "pending"
    return dict(status=status, sample_size=len(expected), reviewed=completed, mismatches=mismatches,
                pending=len(expected) - completed)
