# Real fixture provenance

Saved from the public TED search API on 2026-10-04 during implementation. Original response bytes are unchanged.

SHA-256: `ec23f6c7eb488b0f77c2f855a4dba2b6563d6a96fdae46913b4ab5166dde1933`.

Query: `publication-number IN (543796-2026 543798-2026 543803-2026 680448-2026 680535-2026)`.

Requested fields: `publication-number, notice-identifier, notice-version, notice-type, title-proc, buyer-name, buyer-country, classification-cpv, main-classification-proc, publication-date, deadline-receipt-tender-date-lot, estimated-value-proc, estimated-value-cur-proc, identifier-lot`.

The five records are source-shape examples; 543796-2026 is deliberately outside the main-CPV scope. Tests explicitly modify copied records to exercise failures and generate synthetic IDs only inside test cases. Live HTTP is blocked by conftest.py.

`notice_674236.json` is a derived wrapper containing an unmodified notice object from raw/page-0002.json#/notices/35 of the complete snapshot. Its snapshot_sha256 is the SHA-256 of ted_raw.json (not the page hash). The original page checksum is recorded in that manifest. It supports the real manual-QA regression; synthetic lot fields are added only inside the explicitly labelled test. The separately downloaded XML is archived under docs/source-evidence and is not part of extraction.
