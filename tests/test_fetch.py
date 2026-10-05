import json
from datetime import date

import pytest
import requests

from ted_dataset.fetch import fetch_snapshot, load_snapshot, build_query


class Response:
    def __init__(self, data, status=200, headers=None):
        self.content = json.dumps(data, ensure_ascii=False).encode()
        self.status_code = status
        self.headers = headers or {}


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.headers = {}
        self.payloads = []

    def post(self, url, json, timeout):
        self.payloads.append(dict(json))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def page(notices, count=1, token="next", **extra):
    return Response(dict(notices=notices, totalNoticeCount=count, iterationNextToken=token,
                         timedOut=False, **extra))


def test_window_has_exactly_60_days():
    query = build_query(date(2026, 10, 4))
    assert "20260806 <> 20261004" in query
    assert "main-classification-proc = 48*" in query


def test_iteration_uses_unique_publication_sort():
    # Live regression: date-only ordering returned 3,070 / 3,709 records;
    # publication-number ordering returned all 3,709 on the same date window.
    assert build_query(date(2026, 10, 4)).endswith("SORT BY publication-number DESC")


def test_pagination_raw_bytes_and_offline_load(tmp_path, notice):
    response = page([notice])
    session = Session([response, page([], token="done")])
    run = tmp_path / "run"
    fetch_snapshot(run, date(2026, 10, 4), session=session, sleep=lambda _: None)
    manifest, records = load_snapshot(run)
    assert manifest["status"] == "complete"
    assert manifest["records_retrieved"] == 1
    assert records[0][1] == notice
    assert (run / "raw/page-0001.json").read_bytes() == response.content
    assert "iterationNextToken" not in session.payloads[0]
    assert session.payloads[1]["iterationNextToken"] == "next"
    with pytest.raises(FileExistsError):
        fetch_snapshot(run, date(2026, 10, 4), session=session)


@pytest.mark.parametrize("failure", [
    requests.Timeout("timeout"), Response({}, 503), Response({}, 429, {"Retry-After": "1"}),
    Response({"timedOut": True}),
])
def test_transient_retry_then_success(tmp_path, failure):
    waits = []
    fetch_snapshot(tmp_path / "run", date(2026, 10, 4),
                   session=Session([failure, page([], count=0)]), sleep=waits.append)
    assert len(waits) == 1 and waits[0] >= 1


def test_three_retries_then_incomplete(tmp_path):
    session = Session([Response({}, 503)] * 4)
    with pytest.raises(ValueError):
        fetch_snapshot(tmp_path / "run", date(2026, 10, 4), session=session, sleep=lambda _: None)
    assert len(session.payloads) == 4
    assert json.loads((tmp_path / "run/ted_raw.json").read_text())["status"] == "incomplete"
    with pytest.raises(ValueError, match="incomplete"):
        load_snapshot(tmp_path / "run")


@pytest.mark.parametrize("responses", [
    [Response({"type": "EXPIRED_ITERATION_TOKEN"}, 400)],
    [page([], count=2)],
    [page([{}], count=2, token=None)],
    [page([{}], count=2), page([], count=3)],
    [Response({"notices": {}, "totalNoticeCount": 0, "timedOut": False})],
])
def test_incomplete_data_never_accepted(tmp_path, responses):
    with pytest.raises(ValueError):
        fetch_snapshot(tmp_path / "run", date(2026, 10, 4), session=Session(responses), sleep=lambda _: None)
    assert json.loads((tmp_path / "run/ted_raw.json").read_text())["status"] == "incomplete"


def test_source_tampering_detected(tmp_path):
    run = tmp_path / "run"
    fetch_snapshot(run, date(2026, 10, 4), session=Session([page([], count=0)]))
    (run / "raw/page-0001.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        load_snapshot(run)
