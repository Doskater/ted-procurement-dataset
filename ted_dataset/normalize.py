"""Conservative notice-level normalization; no inferred source facts."""
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from .reference import Reference

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})(Z|[+-](?:0\d|1[0-4]):[0-5]\d)?\Z")
ID_RE = re.compile(r"[1-9]\d*-\d{4}\Z")


def parse_date(raw):
    if not isinstance(raw, str) or not (m := DATE_RE.fullmatch(raw)):
        raise ValueError("Expected XML date with optional timezone")
    zone = m[2] or ""
    if zone.startswith(("+14", "-14")) and not zone.endswith(":00"):
        raise ValueError("Invalid timezone offset")
    return date.fromisoformat(m[1])


def text(value):
    if not isinstance(value, str):
        raise ValueError("Expected string")
    value = " ".join(value.split())
    if any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF or ord(c) in (0xFFFE, 0xFFFF) for c in value):
        raise ValueError("Unsupported text character")
    if len(value) > 32767:
        raise ValueError("Text exceeds Excel cell capacity")
    return value


def strings(value):
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return sorted({text(v) for v in values if v is not None and v != ""} - {""})


def localized(value, multiple=False):
    if value is None:
        return "", ""
    if not isinstance(value, dict):
        raise ValueError("Expected language dictionary")
    for lang in sorted(value, key=lambda k: (k != "eng", k)):
        vals = strings(value[lang])
        if vals:
            if not multiple and len(vals) != 1:
                raise ValueError("Conflicting translated titles")
            return "; ".join(vals), lang
    return "", ""


@dataclass
class Result:
    row: dict
    status: str
    reasons: list[str]
    details: list[str]


def normalize(n, refs: Reference, start: date, end: date):
    row = dict(notice_id="", notice_identifier="", notice_version="", notice_type="",
               title="", title_language="", buyer="", buyer_language="", buyer_country="",
               cpv_code="", cpv_description="", publication_date="", deadline=None,
               estimated_value=None, currency="", source_url="", lot_count=0,
               qa_status="", qa_note="")
    errors, uncertain, notes = [], [], []
    conflicting = set()

    def error(code, detail, ambiguity=False):
        (uncertain if ambiguity else errors).append((code, detail))

    def scalar(key):
        vals = strings(n.get(key))
        if len(vals) > 1:
            conflicting.add(key)
            error("CONFLICTING_SOURCE_VALUES", key, True)
            return ""
        return vals[0] if vals else ""

    if not isinstance(n, dict):
        return Result(row, "rejected", ["PARSING_ERROR"], ["Notice is not an object"])
    try:
        row["notice_id"] = scalar("publication-number")
        if "publication-number" not in conflicting and not ID_RE.fullmatch(row["notice_id"]):
            error("MISSING_REQUIRED_FIELD" if not row["notice_id"] else "INVALID_NOTICE_ID", "publication-number")
        row["notice_identifier"] = scalar("notice-identifier")
        version = n.get("notice-version")
        if version is not None:
            if isinstance(version, bool) or not str(version).isdigit():
                error("CONFLICTING_SOURCE_VALUES", "Invalid notice-version", True)
            else:
                row["notice_version"] = int(version)
        row["notice_type"] = scalar("notice-type")
        if "notice-type" not in conflicting and row["notice_type"] not in {"cn-standard", "cn-social"}:
            error("OUT_OF_SCOPE", "notice-type")
        for target, source, multi in [("title", "title-proc", False), ("buyer", "buyer-name", True)]:
            try:
                row[target], row[target + "_language"] = localized(n.get(source), multi)
                if not row[target]:
                    error("MISSING_REQUIRED_FIELD", source)
            except ValueError as exc:
                error("CONFLICTING_SOURCE_VALUES", f"{source}: {exc}", True)
        row["buyer_country"] = "; ".join(strings(n.get("buyer-country")))
        if not row["buyer_country"]:
            notes.append("MISSING_BUYER_COUNTRY")
        codes = strings(n.get("main-classification-proc"))
        if not codes:
            error("MISSING_REQUIRED_FIELD", "main-classification-proc")
        elif len(codes) > 1:
            error("CONFLICTING_SOURCE_VALUES", "Multiple primary CPV codes", True)
        else:
            code = codes[0]
            row["cpv_code"] = code
            if not re.fullmatch(r"\d{8}", code) or code not in refs.cpv:
                error("INVALID_CPV", code)
            elif not code.startswith(("48", "72")):
                error("OUT_OF_SCOPE", code)
            else:
                row["cpv_description"] = refs.cpv[code]
        try:
            published = parse_date(n.get("publication-date"))
            row["publication_date"] = published.isoformat()
            if not start <= published <= end:
                error("OUT_OF_SCOPE", "publication-date outside window")
        except ValueError:
            error("INVALID_DATE", "publication-date")
        url = n.get("links", {}).get("html", {}).get("ENG", "")
        row["source_url"] = text(url)
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.netloc != "ted.europa.eu" or
                ("publication-number" not in conflicting and parsed.path != f"/en/notice/-/detail/{row['notice_id']}") or
                parsed.query or parsed.fragment):
            error("INVALID_URL", "Expected exact TED English detail URL for publication number")
        lots = strings(n.get("identifier-lot"))
        row["lot_count"] = len(lots)
        if len(lots) != 1:
            notes.append("MULTI_LOT_DEADLINE_OMITTED" if lots else "UNKNOWN_LOT_STRUCTURE")
        else:
            try:
                deadlines = strings(n.get("deadline-receipt-tender-date-lot"))
                if not deadlines:
                    notes.append("MISSING_DEADLINE")
                elif len(deadlines) > 1:
                    notes.append("AMBIGUOUS_DEADLINE")
                else:
                    row["deadline"] = parse_date(deadlines[0]).isoformat()
            except ValueError:
                notes.append("INVALID_DEADLINE")
        raw_value = n.get("estimated-value-proc")
        raw_currency = n.get("estimated-value-cur-proc")
        if raw_value is None or raw_value == "":
            notes.append("MISSING_PROCEDURE_ESTIMATED_VALUE")
            if raw_currency:
                notes.append("CURRENCY_WITHOUT_VALUE_OMITTED")
        else:
            try:
                if isinstance(raw_value, bool) or not isinstance(raw_value, (str, int, float, Decimal)):
                    raise ValueError("Not a numeric scalar")
                amount = Decimal(str(raw_value))
                if not amount.is_finite() or amount <= 0:
                    raise ValueError("Non-positive or non-finite value")
                # Excel numeric precision is limited; never silently round a source value.
                if len(amount.normalize().as_tuple().digits) > 15 or amount > Decimal("1e15"):
                    raise ValueError("Value exceeds exact delivery precision")
                row["estimated_value"] = amount
            except (InvalidOperation, ValueError):
                error("INVALID_VALUE", "estimated-value-proc", True)
            if not isinstance(raw_currency, str) or raw_currency not in refs.currencies:
                error("INVALID_CURRENCY", "Missing or unknown currency for published value", True)
            else:
                row["currency"] = raw_currency
    except (ValueError, TypeError, AttributeError) as exc:
        error("PARSING_ERROR", str(exc))
    status = "rejected" if errors else "uncertain" if uncertain else "accepted"
    row["qa_status"], row["qa_note"] = status, "; ".join(notes)
    all_issues = errors + uncertain
    return Result(row, status, sorted({x[0] for x in all_issues}), [x[1] for x in all_issues])
