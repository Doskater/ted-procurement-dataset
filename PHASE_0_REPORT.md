# Source investigation

Snapshot date: 4 October 2026.

## API and query

Public endpoint: `POST https://api.ted.europa.eu/v3/notices/search`.

```text
publication-date = (20260806 <> 20261004)
AND (main-classification-proc = 48* OR main-classification-proc = 72*)
AND notice-type IN (cn-standard cn-social)
SORT BY publication-number DESC
```

Options: scope=ALL, onlyLatestVersions=true, paginationMode=ITERATION, limit=250. Exact request bodies and response checksums are recorded in the snapshot manifest. The complete iteration returned 3,709 records and ended with an empty sixteenth page.

A previous attempt using publication-date ordering returned only 3,070 of 3,709 records. It was rejected as incomplete. Publication-number ordering resolved the observed discrepancy; the server-side cause was not established.

## Five inspected records

| Publication | Main CPV | Finding |
|---|---|---|
| 543796-2026 | 79000000 | Additional IT codes do not make this notice eligible. |
| 543798-2026 | 48000000 | German title; procedure estimate supplied as string 1000 EUR. |
| 543803-2026 | 48900000 | Portuguese title; procedure estimate 499318 EUR. |
| 680448-2026 | 72267000 | Version 2; procedure estimate absent. |
| 680535-2026 | 72000000 | Dutch title; procedure estimate absent. |

The unchanged five-record response is saved in tests/fixtures/ted_sample_response.json. Its query and checksum are documented alongside it.

## Observed field shapes

| Field | Shape |
|---|---|
| publication-number | String such as 543798-2026 |
| title-proc | Language dictionary with text values |
| buyer-name | Language dictionary with arrays of names |
| buyer-country | Array of country codes |
| main-classification-proc | Array, sometimes with repeated codes |
| publication-date | Calendar date with optional timezone, e.g. 2026-08-06+02:00 |
| identifier-lot | Array of lot identifiers |
| deadline-receipt-tender-date-lot | Array of calendar dates |
| estimated-value-proc | Numeric string or absent |
| estimated-value-cur-proc | Currency code or absent |
| links.html.ENG | English TED detail URL |

The response envelope contains notices, totalNoticeCount, iterationNextToken and timedOut. CPV descriptions come from the official CPV 2008 XML archive (9,454 English entries); currencies come from the pinned SIX ISO 4217 list. Sources and checksums are retained in data/reference/manifest.json.

Decisions: main CPV only; procedure-level amounts only; no lot/date positional matching; original language retained; source calendar dates preserved; complete collection before selection; unresolved records kept outside delivery.
