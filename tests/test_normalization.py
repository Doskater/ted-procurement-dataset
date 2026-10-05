import copy
from datetime import date
from decimal import Decimal

import pytest

from ted_dataset.normalize import normalize, parse_date
from ted_dataset.validate import process_records


def run(n, refs):
    return normalize(n, refs, date(2026, 8, 6), date(2026, 10, 4))


def test_real_notice(notice, refs):
    r = run(notice, refs)
    assert r.status == "accepted"
    assert r.row["notice_id"] == "543798-2026"
    assert r.row["title"] == "Blackberry UEM Software-Lizenzen KRH"
    assert r.row["title_language"] == "deu"
    assert r.row["publication_date"] == "2026-08-06"
    assert r.row["estimated_value"] == Decimal("1000")
    assert r.row["cpv_description"] == "Software package and information systems"


@pytest.mark.parametrize("field,value,reason", [
    ("title-proc", {}, "MISSING_REQUIRED_FIELD"),
    ("buyer-name", {}, "MISSING_REQUIRED_FIELD"),
    ("publication-date", "2026-02-30Z", "INVALID_DATE"),
    ("main-classification-proc", ["79000000"], "OUT_OF_SCOPE"),
    ("main-classification-proc", ["72999999"], "INVALID_CPV"),
    ("main-classification-proc", [], "MISSING_REQUIRED_FIELD"),
    ("notice-type", "can-standard", "OUT_OF_SCOPE"),
    ("publication-date", "2025-01-01Z", "OUT_OF_SCOPE"),
    ("links", {"html": {"ENG": "https://ted.europa.eu.evil.test/543798-2026"}}, "INVALID_URL"),
    ("links", {"html": {"ENG": "https://ted.europa.eu/en/notice/-/detail/1-2026"}}, "INVALID_URL"),
])
def test_rejected_defects(notice, refs, field, value, reason):
    notice[field] = value
    r = run(notice, refs)
    assert r.status == "rejected"
    assert reason in r.reasons


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-2", "0", "oops", "1,000", True])
def test_invalid_money_uncertain(notice, refs, value):
    notice["estimated-value-proc"] = value
    assert run(notice, refs).status == "uncertain"


def test_missing_value_allowed(notice, refs):
    notice.pop("estimated-value-proc", None)
    r = run(notice, refs)
    assert r.status == "accepted" and r.row["estimated_value"] is None


@pytest.mark.parametrize("currency", [None, "XXX", "ZZZ", ""])
def test_bad_currency_uncertain(notice, refs, currency):
    notice["estimated-value-cur-proc"] = currency
    assert run(notice, refs).status == "uncertain"


def test_language_preference_and_multi_buyer(notice, refs):
    notice["title-proc"] = {"fra": "titre", "deu": "titel", "eng": " English  title "}
    notice["buyer-name"] = {"eng": ["Buyer B", "Buyer A", "Buyer B"]}
    notice["buyer-country"] = ["FRA", "DEU", "FRA"]
    r = run(notice, refs).row
    assert r["title"] == "English title"
    assert r["buyer"] == "Buyer A; Buyer B"
    assert r["buyer_country"] == "DEU; FRA"
    notice["title-proc"].pop("eng")
    assert run(notice, refs).row["title_language"] == "deu"


def test_repeated_cpv_is_not_a_conflict(notice, refs):
    notice["main-classification-proc"] *= 2
    assert run(notice, refs).status == "accepted"


def test_multiple_main_codes_uncertain(notice, refs):
    notice["main-classification-proc"] = ["48000000", "72000000"]
    assert run(notice, refs).status == "uncertain"


@pytest.mark.parametrize("lots,deadlines,note", [
    (["LOT-1", "LOT-2"], ["2026-09-07Z"], "MULTI_LOT_DEADLINE_OMITTED"),
    (["LOT-1"], [], "MISSING_DEADLINE"),
    (["LOT-1"], ["2026-09-07Z", "2026-09-08Z"], "AMBIGUOUS_DEADLINE"),
    (["LOT-1"], ["2026-02-30Z"], "INVALID_DEADLINE"),
])
def test_optional_deadline_blank(notice, refs, lots, deadlines, note):
    notice["identifier-lot"] = lots
    notice["deadline-receipt-tender-date-lot"] = deadlines
    r = run(notice, refs)
    assert r.status == "accepted"
    assert r.row["deadline"] is None and note in r.row["qa_note"]


@pytest.mark.parametrize("raw", ["2026-10-02+02:00", "2026-10-02Z", "2026-10-02"])
def test_date_preserves_calendar_day(raw):
    assert parse_date(raw) == date(2026, 10, 2)


@pytest.mark.parametrize("raw", ["2026-10-02+99:00", "2026-10-02junk", "2026-02-30", "2026-10-02T00:00:00Z"])
def test_invalid_date_shape(raw):
    with pytest.raises(ValueError):
        parse_date(raw)


def process(records, refs, target=300):
    return process_records([(f"page.json#{i}", n) for i, n in enumerate(records)], refs,
                           date(2026, 8, 6), date(2026, 10, 4), target)


def test_duplicate_and_reconciliation(notice, refs):
    r = process([notice, copy.deepcopy(notice)], refs)
    assert len(r.selected) == 1
    assert r.metrics["duplicates"] == 1
    assert len(r.ledger) == 2
    assert r.metrics["raw_records"] == sum(r.metrics[k] for k in ("valid_unique", "rejected", "uncertain", "duplicates"))


def test_conflicting_group_all_uncertain(notice, refs):
    other = copy.deepcopy(notice)
    other["title-proc"]["deu"] = "Conflicting title"
    r = process([notice, notice, other], refs)
    assert r.metrics["uncertain"] == 3 and r.metrics["duplicates"] == 0
    assert not r.selected


def test_missing_ids_do_not_merge(notice, refs):
    notice.pop("publication-number")
    r = process([notice, notice], refs)
    assert r.metrics["rejected"] == 2


def test_select_latest_300_and_keep_surplus(notice, refs):
    records = []
    for i in range(305):
        n = copy.deepcopy(notice)
        n["publication-number"] = f"{1000+i}-2026"
        n["links"]["html"]["ENG"] = f"https://ted.europa.eu/en/notice/-/detail/{1000+i}-2026"
        records.append(n)
    r = process(records, refs)
    assert len(r.selected) == 300 and len(r.not_selected) == 5
    assert r.selected[0]["notice_id"] == "1304-2026"
    assert process(list(reversed(records)), refs).selected == r.selected
