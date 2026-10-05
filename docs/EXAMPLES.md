# Evidence examples

All examples below come from the archived 2026-10-04 collection. None are synthetic.

## 1. Raw source → delivered row

Publication [681454-2026](https://ted.europa.eu/en/notice/-/detail/681454-2026); source pointer `raw/page-0001.json#/notices/0`.

Source excerpt (the full unchanged response remains in the raw page):

```json
{
  "publication-number": "681454-2026",
  "title-proc": {
    "pol": "Modernizacja istniejącego systemu priorytetów dla pojazdów transportu zbiorowego"
  },
  "buyer-name": {
    "pol": [
      "Zarząd Dróg Miejskich"
    ]
  },
  "main-classification-proc": [
    "72260000"
  ],
  "publication-date": "2026-10-02+02:00",
  "deadline-receipt-tender-date-lot": [
    "2026-11-03+01:00"
  ]
}
```

| Output field | Delivered value |
|---|---|
| notice_id | 681454-2026 |
| title | Modernizacja istniejącego systemu priorytetów dla pojazdów transportu zbiorowego |
| title_language | pol |
| buyer | Zarząd Dróg Miejskich |
| buyer_country | POL |
| cpv_code | 72260000 |
| cpv_description | Software-related services |
| publication_date | 2026-10-02 |
| deadline | 2026-11-03 |
| estimated_value | (blank) |
| qa_note | MISSING_PROCEDURE_ESTIMATED_VALUE |

The timezone-bearing publication date keeps its calendar day. The repeated additional CPV is irrelevant to the main-code selection. No English title was supplied, so the Polish source title is retained.

## 2. Missing and problematic data

The notice above has no procedure estimate. It remains accepted with a blank amount and `MISSING_PROCEDURE_ESTIMATED_VALUE`; no zero is invented.

By contrast, [676179-2026](https://ted.europa.eu/en/notice/-/detail/676179-2026) has `estimated-value-proc="0"` at `raw/page-0001.json#/notices/216`. It is **uncertain**, reason `INVALID_VALUE`, and is excluded from the 300 delivered rows.

All 63 uncertain occurrences have a source zero: 48 use `"0"`, and 15 use `"0.00"`. There were no duplicate occurrences or definitive rejections in this collection; those paths are tested using explicitly modified fixtures.

Multi-lot example: [681142-2026](https://ted.europa.eu/en/notice/-/detail/681142-2026) has 7 distinct lots. The exported deadline is blank with `MULTI_LOT_DEADLINE_OMITTED`. No positional match between lot IDs and date arrays is assumed.

## 3. Actual QA metrics

| Metric | Count |
|---|---:|
| raw_records | 3709 |
| valid_unique | 3646 |
| selected | 300 |
| valid_not_selected | 3346 |
| rejected | 0 |
| uncertain | 63 |
| duplicates | 0 |
| target | 300 |
| duplicate_selected_ids | 0 |
| selected_with_value | 129 |
| selected_with_deadline | 207 |

`3709 = 3646 + 0 + 63 + 0`; `3646 = 300 + 3346`.

Of the delivered 300 rows, 129 have estimates and 207 have usable single-lot deadlines. The remaining 171 estimates and 93 deadlines are blank with explicit notes. Manual sample: 20 records, seed 42, review completed. One observation about a lot-level estimate was resolved; see QUALITY_NOTES.md.
