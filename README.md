# TED procurement notices → validated Excel dataset

**Independent public-data project.** Python extraction and validation of software and IT procurement notices from Tenders Electronic Daily (TED).

The delivery contains **300 notices** published within 6 August–4 October 2026, with source links, a data dictionary and a record-level audit trail.

| Result | Records |
|---|---:|
| Retrieved from TED | 3,709 |
| Valid unique notices | 3,646 |
| Selected for delivery | 300 |
| Valid notices kept separately | 3,346 |
| Quarantined: zero procedure estimate | 63 |
| Duplicate occurrences | 0 |

**77 offline tests passed. A 20-record manual sample was reviewed with no unresolved discrepancies.** The sample review does not imply that every delivered record was checked manually.

## Files

- [Excel workbook](delivery/validated_notices.xlsx) — Notices, QA Summary, Data Dictionary and Rejected sheets.
- [CSV dataset](delivery/validated_notices.csv), [valid surplus](delivery/valid_not_selected.csv), [quarantine](delivery/rejected_or_uncertain.csv) and [record ledger](delivery/record_ledger.csv).
- [QA report](delivery/QA_REPORT.md) and [completed review sample](delivery/qa/manual_qa_sample.csv).
- [Data dictionary](docs/DATA_DICTIONARY.md), [three worked examples](docs/EXAMPLES.md) and [quality notes](docs/QUALITY_NOTES.md).
- [Source investigation](PHASE_0_REPORT.md) and [Russian review instructions](docs/MANUAL_QA_RU.md).

## Scope

Main procedure CPV starts with `48` or `72`; notice type is `cn-standard` or `cn-social`. All TED countries are included. The API is asked for latest versions only. All matching records are retrieved before the most recent 300 valid notices are selected by publication date and numeric publication number, both descending.

This is a snapshot of published notices, not a list of guaranteed open tenders. A new fetch uses a 60-day inclusive window ending on `--as-of`, or today's date in Europe/Minsk. The window is never expanded automatically.

## Run

Python 3.11+; verified with Python 3.12. Run commands from the repository root.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python tools/verify.py

# Replay the archived snapshot without network access.
python -m ted_dataset process --run data/runs/2026-10-04 --output data/replays/001

# Update the supplied report from the completed review sample.
python -m ted_dataset report --run data/runs/2026-10-04 --output delivery
```

For a new live collection, choose a new run directory:

```bash
python -m ted_dataset fetch --as-of 2026-10-04 --run data/runs/new-001
python -m ted_dataset process --run data/runs/new-001
```

`fetch` and `process` refuse existing destinations. Failed or incomplete collections cannot be processed. Start a separate collection after an expired token or exhausted retries. `report` preserves the review CSV and checks snapshot, reference, delivery and processing-code fingerprints. If package code or pinned dependencies change, reprocess into a new directory before reviewing that version.

## Data rules

- Source English text is preferred; otherwise the first nonempty language code is selected alphabetically. Original language is recorded; no translation is performed.
- Buyers and country codes are deduplicated independently. Lists are not matched by position.
- Publication dates keep the source calendar day. Tender deadlines are included only for an unambiguous single-lot notice.
- Estimated value comes only from `estimated-value-proc`, with its procedure currency. Lot values are never substituted or summed, including for a single lot. Missing procedure estimates remain blank with an explicit QA note.
- Nonpositive, malformed or unsafe-to-export amounts are quarantined. CPV and currency codes use pinned official reference files.
- Identical valid duplicates collapse. Conflicting records sharing a publication number are quarantined. Different publication numbers are not merged by title.

Each source occurrence receives one ledger outcome:

```text
3709 = 3646 valid unique + 0 rejected + 63 uncertain + 0 duplicates
3646 = 300 selected + 3346 valid not selected
```

## Reproducibility and spreadsheet handling

Raw response bodies are saved unchanged under `data/runs/2026-10-04/raw`. `ted_raw.json` is an index containing requests, counts, retrieval times and SHA-256 checksums. Raw pointers use zero-based array positions, for example `raw/page-0002.json#/notices/35`. Reference files are preserved with their sources and checksums.

The workbook stores identifiers and source strings as text, dates as dates, and estimates as numbers. It includes filters, frozen headers and clickable source URLs. Exported cells are reread and executable formulas are rejected.

CSV uses UTF-8 with BOM and preserves literal source text. Import all columns as Text first, then explicitly convert date and amount columns as needed. Do not rely on double-click auto-detection; use the XLSX for routine viewing.

## Sources

[TED API specification](https://api.ted.europa.eu/api-v3.yaml), [TED search documentation](https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html), [official CPV dictionary](https://ted.europa.eu/en/simap/cpv), [SIX ISO 4217 list](https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml).
