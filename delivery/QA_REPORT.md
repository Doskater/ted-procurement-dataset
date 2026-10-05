# QA Report

Automated checks passed; manual sample verification passed.

Independent public-data project. Not client work.

Source: Tenders Electronic Daily (TED). Retrieved: 2026-10-04T11:11:15.871779+00:00.
Publication window: 2026-08-06 through 2026-10-04 (inclusive).
Snapshot SHA-256: `8579e3490b10c06439682b8967de7f29d470c00210eec678a9d31e9e069d2329`.

## Retrieval and reconciliation

Source reported: **3709**. Retrieved: **3709**.
All successful page checksums verified; iteration ended with an empty page.

| Metric | Count |
|---|---:|
| raw records | 3709 |
| valid unique | 3646 |
| selected | 300 |
| valid not selected | 3346 |
| rejected | 0 |
| uncertain | 63 |
| duplicates | 0 |
| target | 300 |
| duplicate selected ids | 0 |
| selected with value | 129 |
| selected with deadline | 207 |

`3709 = 3646 valid unique + 0 rejected + 63 uncertain + 0 duplicate occurrences`
`3646 = 300 selected + 3346 valid not selected`

Every source occurrence has one entry in record_ledger.csv. Rejections retain reasons and raw pointers.

## Automated verification

Test evidence: **passed**.
Tests: 77; failures: 0; errors: 0.
Selected IDs are unique. Required values, dates, CPV membership, exact source URLs and export readback passed.
Test fixtures are offline. Deliberately corrupted inputs are confined to tests.

## Manual sample verification

Seed: 42. Sample: 20. Reviewed: 20. Pending: 0. Mismatching records: 0.
Review status is read from qa/manual_qa_sample.csv; the program never marks source checks as a human pass.

## Known limitations

- Snapshot of published contract notices, not a guarantee of currently open opportunities or bidder eligibility.
- Latest-version filtering relies on TED. Publication number is the row identity; different publications are not merged by title or UUID.
- A procedure's main CPV must start with 48 or 72. IT mentioned only in additional codes/lots is excluded.
- Only cn-standard and cn-social notices are included, across all TED buyer countries.
- Titles and buyer names retain source languages; English labels do not imply translated source content.
- Multi-lot or ambiguous deadlines are intentionally blank. Single-lot tender dates omit time of day.
- Estimates are procedure-level source values only. No lot summation, currency conversion, VAT inference or accuracy warranty for publisher-entered amounts.
- MISSING_PROCEDURE_ESTIMATED_VALUE means absent at procedure level; a lot may still publish an estimate. A single-lot estimate is not substituted for the procedure field.
- ISO currency validation uses the pinned current SIX list; obsolete/unknown codes are quarantined.
- Manual verification covers the sample only. Public source pages may change after capture; compare the same publication ID and the archived raw response.
- CSV retains literal text; import with explicit text types. XLSX stores untrusted source strings as text, never formulas.
