"""Read-only TED retrieval with immutable pages and explicit completeness."""
import json
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

from .common import digest, read_json, safe_path, utc_now, write_json

ENDPOINT = "https://api.ted.europa.eu/v3/notices/search"
FIELDS = ["publication-number", "notice-identifier", "notice-version", "notice-type",
          "title-proc", "buyer-name", "buyer-country", "classification-cpv",
          "main-classification-proc", "publication-date", "deadline-receipt-tender-date-lot",
          "estimated-value-proc", "estimated-value-cur-proc", "identifier-lot"]


def build_query(as_of: date):
    start = as_of - timedelta(days=59)
    return (f"publication-date = ({start:%Y%m%d} <> {as_of:%Y%m%d}) "
            "AND (main-classification-proc = 48* OR main-classification-proc = 72*) "
            "AND notice-type IN (cn-standard cn-social) SORT BY publication-number DESC")


def retry_delay(header, attempt):
    if header:
        try:
            return max(0, float(header))
        except ValueError:
            try:
                return max(0, (parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return 2 ** attempt


def fetch_snapshot(directory, as_of, *, session=None, sleep=time.sleep):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "raw").mkdir()
    (directory / "diagnostics").mkdir()
    manifest = dict(schema_version=1, source="Tenders Electronic Daily", endpoint=ENDPOINT,
                    retrieved_at=utc_now(), as_of=as_of.isoformat(),
                    date_start=(as_of - timedelta(days=59)).isoformat(),
                    query=build_query(as_of), cpv_prefixes=["48", "72"], status="incomplete",
                    source_total=None, records_retrieved=0, pages=[], attempts=[])
    write_json(directory / "ted_raw.json", manifest)
    own_session = session is None
    session = session or requests.Session()
    session.headers.update({"User-Agent": "TED-Validated-Dataset/1.0 (independent public-data project)"})
    payload = dict(query=manifest["query"], fields=FIELDS, limit=250, scope="ALL",
                   paginationMode="ITERATION", onlyLatestVersions=True)
    try:
        page_number = 1
        while True:
            body = None
            for attempt in range(4):
                event = dict(page=page_number, attempt=attempt + 1, retrieved_at=utc_now(), request=dict(payload))
                retry_after = None
                try:
                    response = session.post(ENDPOINT, json=payload, timeout=(10, 60))
                    event["http_status"] = response.status_code
                    # Keep every returned body, including server errors, without rewriting.
                    name = f"diagnostics/page-{page_number:04d}-attempt-{attempt+1}.json"
                    (directory / name).write_bytes(response.content)
                    event.update(file=name, sha256=digest(response.content))
                    if response.status_code == 429 or 500 <= response.status_code < 600:
                        retry_after = response.headers.get("Retry-After")
                        event["error"] = f"Transient HTTP {response.status_code}"
                    elif response.status_code != 200:
                        raise ValueError(f"Non-retryable HTTP {response.status_code}: {response.content[:500]!r}")
                    else:
                        parsed = json.loads(response.content, parse_float=Decimal)
                        if not isinstance(parsed, dict):
                            raise ValueError("Response must be an object")
                        if parsed.get("timedOut") is True:
                            event["error"] = "TED search timed out"
                        else:
                            body = parsed
                except (requests.RequestException, json.JSONDecodeError) as exc:
                    event["error"] = str(exc)
                finally:
                    manifest["attempts"].append(event)
                    write_json(directory / "ted_raw.json", manifest)
                if body is not None:
                    break
                if attempt == 3:
                    raise ValueError("Retrieval exhausted three retries")
                sleep(retry_delay(retry_after, attempt))
            notices = body.get("notices")
            count = body.get("totalNoticeCount")
            if (not isinstance(notices, list) or type(count) is not int or count < 0 or
                    body.get("timedOut") is not False):
                raise ValueError("Invalid response envelope")
            if manifest["source_total"] is None:
                manifest["source_total"] = count
            if count != manifest["source_total"]:
                raise ValueError("Source count changed inside iteration")
            name = f"raw/page-{page_number:04d}.json"
            (directory / name).write_bytes(response.content)
            manifest["pages"].append(dict(file=name, sha256=digest(response.content),
                                           count=len(notices), retrieved_at=utc_now(), request=dict(payload)))
            manifest["records_retrieved"] += len(notices)
            write_json(directory / "ted_raw.json", manifest)
            if manifest["records_retrieved"] > count:
                raise ValueError("More records received than source count")
            if not notices:
                if manifest["records_retrieved"] != count:
                    raise ValueError("Empty page before source count reconciles")
                break
            token = body.get("iterationNextToken")
            if not isinstance(token, str) or not token:
                raise ValueError("Missing iteration token")
            payload["iterationNextToken"] = token
            page_number += 1
        manifest["status"] = "complete"
        manifest["completed_at"] = utc_now()
    except BaseException as exc:
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        write_json(directory / "ted_raw.json", manifest)
        if own_session:
            session.close()
    return directory


def load_snapshot(directory):
    directory = Path(directory)
    manifest = read_json(directory / "ted_raw.json")
    if manifest.get("status") != "complete":
        raise ValueError("Snapshot is incomplete")
    if manifest.get("endpoint") != ENDPOINT or manifest.get("query") != build_query(date.fromisoformat(manifest["as_of"])):
        raise ValueError("Snapshot query is outside this project's supported scope")
    if manifest.get("date_start") != (date.fromisoformat(manifest["as_of"]) - timedelta(days=59)).isoformat():
        raise ValueError("Snapshot date window mismatch")
    records, files = [], set()
    pages = manifest["pages"]
    if not pages:
        raise ValueError("No pages in snapshot")
    expected_request = dict(query=manifest["query"], fields=FIELDS, limit=250, scope="ALL",
                            paginationMode="ITERATION", onlyLatestVersions=True)
    for i, entry in enumerate(pages):
        if entry.get("request") != expected_request or entry["request"].get("onlyLatestVersions") is not True:
            raise ValueError("Snapshot request or iteration chain mismatch")
        if entry["file"] in files:
            raise ValueError("Repeated page in manifest")
        files.add(entry["file"])
        raw = safe_path(directory, entry["file"]).read_bytes()
        if digest(raw) != entry["sha256"]:
            raise ValueError("Raw page checksum mismatch")
        page = json.loads(raw, parse_float=Decimal)
        if (page.get("timedOut") is not False or page.get("totalNoticeCount") != manifest["source_total"]
                or not isinstance(page.get("notices"), list) or len(page["notices"]) != entry["count"]):
            raise ValueError("Page metadata mismatch")
        if not page["notices"] and i != len(pages) - 1:
            raise ValueError("Empty non-terminal page")
        if page["notices"]:
            token = page.get("iterationNextToken")
            if not isinstance(token, str) or not token:
                raise ValueError("Missing iteration token")
            expected_request["iterationNextToken"] = token
        records.extend((f"{entry['file']}#/notices/{j}", n) for j, n in enumerate(page["notices"]))
    if pages[-1]["count"] != 0 or len(records) != manifest["source_total"] or len(records) != manifest["records_retrieved"]:
        raise ValueError("Snapshot reconciliation failed")
    return manifest, records
