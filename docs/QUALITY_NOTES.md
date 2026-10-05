# Quality notes

## Collection

The initial date-sorted iteration returned 3,070 records against a reported total of 3,709 and was rejected as incomplete. A separate collection ordered by publication number retrieved all 3,709 records. That complete collection is included here. Final dataset ordering remains publication date, then numeric publication number, descending.

## Manual review: 674236-2026

The 20-record review sample identified one apparent discrepancy: notice 674236-2026 displays 401698.90 PLN, while the procedure estimate in the dataset is blank.

The [official XML](https://ted.europa.eu/en/notice/674236-2026/xml) places this amount under `ProcurementProjectLot/ProcurementProject/RequestedTenderTotal/EstimatedOverallContractAmount` for LOT-0001. No estimate occurs at the direct procedure path `ProcurementProject/RequestedTenderTotal/EstimatedOverallContractAmount`. The archived XML and checksum are in [source-evidence](source-evidence/).

The blank procedure value is correct under the dataset's field mapping. The original note was clarified from MISSING_ESTIMATED_VALUE to MISSING_PROCEDURE_ESTIMATED_VALUE. This changed only notes on 171 delivered rows and 1,672 surplus rows; all business values, identities, ordering and counts stayed unchanged.

The reviewer accepted the scope distinction. The procedure value check is recorded as not_applicable, with the published lot amount retained in review_notes. Existing checks were carried forward after the note-only revision; a second full source review was not claimed. The original mismatch remains in the retained development audit. Current sample: 20 reviewed, 0 pending, 0 unresolved mismatches.

## Automated checks

77 offline tests cover normalization, CPV/date/currency checks, missing and invalid values, duplicate conflicts, pagination and retries, incomplete snapshots, reconciliation, selection, export readback and review integrity. Real saved fixtures are distinguished from explicit test corruptions. Tests block live HTTP.

The complete snapshot was processed twice offline with identical CSV rows, order and metrics. CSV and XLSX values were compared, and workbook previews inspected. Test evidence is in `verification/evidence.json`; its code fingerprint and JUnit checksum are validated when generating the report.
