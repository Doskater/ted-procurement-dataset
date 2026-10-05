# Data dictionary

 Empty optional values are blank, not zero.

| Column | Definition |
|---|---|
| notice_id | Unique TED publication-number. Text, not procedure ID. |
| title | Procedure title in source English if present, otherwise alphabetically first language code. No translation. |
| buyer | Sorted distinct names in chosen source language, joined with semicolons. |
| buyer_country | Sorted country codes from TED; not paired positionally with buyer names. |
| cpv_code | Single procedure-level main CPV, eight-digit text; prefixes 48 or 72. |
| cpv_description | Official English CPV 2008 description. |
| publication_date | Source calendar date. Timezone suffix validated without UTC day shifting. |
| deadline | Tender submission date for a single-lot notice only. Blank with QA note otherwise. No active-status guarantee. |
| estimated_value | Positive procedure-level estimate (estimated-value-proc). Blank if absent there, even when the sole lot has an estimate. No lot fallback, lot sums or currency conversion. |
| currency | Source ISO 4217 code paired with published value. Blank when value is absent. |
| source_url | Exact English detail URL returned by TED for this publication number. |
| qa_status | accepted means automatic record rules passed, not human review completed. |
| qa_note | Missing optional values and omitted ambiguous deadlines. MISSING_PROCEDURE_ESTIMATED_VALUE means absent at procedure level; it does not assert that lot estimates are absent. |
| notice_identifier | Source notice UUID, distinct from publication number and procurement procedure ID. |
| notice_version | Source version number, if present. Latest versions requested from TED. |
| notice_type | cn-standard or cn-social. |
| title_language | Language key of selected title; original content retained. |
| buyer_language | Language key of selected buyer names. |
| lot_count | Number of distinct lot identifiers present in this response; zero means unknown. |
