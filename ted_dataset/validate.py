"""Disjoint record dispositions, deduplication and deterministic selection."""
from collections import Counter, defaultdict
from dataclasses import dataclass

from .common import canonical, digest
from .normalize import normalize


@dataclass
class Processed:
    selected: list[dict]
    not_selected: list[dict]
    rejected: list[dict]
    ledger: list[dict]
    metrics: dict


def process_records(records, refs, start, end, target=300):
    if target < 1:
        raise ValueError("Target must be positive")
    groups = defaultdict(list)
    for ref, n in records:
        normalized = normalize(n, refs, start, end)
        key = normalized.row["notice_id"] or f"missing:{ref}"
        groups[key].append((ref, n, normalized))
    valid, rejected, ledger = [], [], []
    for group in groups.values():
        fingerprints = {digest(canonical(n).encode()) for _, n, _ in group}
        conflict = len(fingerprints) > 1
        for index, (ref, n, r) in enumerate(group):
            if conflict:
                r.status = "uncertain"
                r.reasons = ["CONFLICTING_SOURCE_VALUES"]
                r.details = ["Same publication number has different source payloads; all occurrences quarantined"]
            status = r.status
            if status == "accepted":
                if index:
                    status = "duplicate"
                else:
                    valid.append(r.row)
            if status in ("rejected", "uncertain"):
                rejected.append(dict(notice_id=r.row["notice_id"], title=r.row["title"],
                                     source_url=r.row["source_url"], status=status, raw_ref=ref,
                                     reason_code="; ".join(r.reasons), reason_detail="; ".join(r.details)))
            ledger.append(dict(raw_ref=ref, notice_id=r.row["notice_id"], disposition=status,
                               reason_code="DUPLICATE_NOTICE" if status == "duplicate" else "; ".join(r.reasons)))
    valid.sort(key=lambda r: (r["publication_date"], int(r["notice_id"].split("-")[0])), reverse=True)
    selected, surplus = valid[:target], valid[target:]
    selected_ids = {r["notice_id"] for r in selected}
    if len({r["notice_id"] for r in valid}) != len(valid):
        raise ValueError("Duplicate valid notice IDs")
    for entry in ledger:
        if entry["disposition"] == "accepted":
            entry["disposition"] = "selected" if entry["notice_id"] in selected_ids else "not_selected"
    counts = Counter(e["disposition"] for e in ledger)
    metrics = dict(raw_records=len(records), valid_unique=len(valid), selected=len(selected),
                   valid_not_selected=len(surplus), rejected=counts["rejected"], uncertain=counts["uncertain"],
                   duplicates=counts["duplicate"], target=target,
                   duplicate_selected_ids=len(selected) - len(selected_ids),
                   selected_with_value=sum(r["estimated_value"] is not None for r in selected),
                   selected_with_deadline=sum(r["deadline"] is not None for r in selected))
    if len(records) != len(valid) + metrics["rejected"] + metrics["uncertain"] + metrics["duplicates"]:
        raise ValueError("Processing reconciliation failed")
    if len(valid) != len(selected) + len(surplus) or len(ledger) != len(records):
        raise ValueError("Selection reconciliation failed")
    return Processed(selected, surplus, rejected, ledger, metrics)
