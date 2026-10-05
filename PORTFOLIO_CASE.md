# Public Procurement Data Extraction & Excel Validation

**Independent public-data project**

I built a Python pipeline that retrieves public TED procurement notices and delivers a validated Excel and CSV dataset.

The collection covered 3,709 software and IT procurement notices. After validation, 300 recent notices were selected for delivery, 3,346 valid records were kept separately, and 63 records with zero procedure estimates were quarantined.

The workbook includes source links, a data dictionary, a QA summary and excluded records. Raw API responses, checksums and a record ledger support offline reproduction. Validation covers multilingual fields, CPV codes, dates, currencies, missing values and duplicate conflicts.

77 automated tests passed. A 20-record manual sample was reviewed; one observation was resolved by distinguishing a lot estimate from a procedure estimate.

Tools: Python, requests, openpyxl, pytest, CSV, JSON.

Publication window: 6 August–4 October 2026. This is a snapshot of published notices; it does not guarantee that bidding remains open.
