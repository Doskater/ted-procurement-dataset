"""Explicitly constructed edge cases found during independent review."""
import copy
import json
from datetime import date
from decimal import Decimal

import pytest

from ted_dataset.common import read_json, write_json
from ted_dataset.fetch import fetch_snapshot, load_snapshot
from ted_dataset.normalize import normalize
from ted_dataset.validate import process_records
from ted_dataset.pipeline import process_snapshot, update_report
from test_fetch import Session, page

START, END = date(2026, 8, 6), date(2026, 10, 4)


def test_numeric_json_money_preserves_source_precision(tmp_path, notice, refs):
    response = page([notice])
    payload = json.loads(response.content)
    payload['notices'][0]['estimated-value-proc'] = 'NUMBER_PLACEHOLDER'
    response.content = json.dumps(payload).replace('"NUMBER_PLACEHOLDER"', '999999999999999.99').encode()
    run = tmp_path/'run'
    fetch_snapshot(run, END, session=Session([response, page([])]))
    _, records = load_snapshot(run)
    assert records[0][1]['estimated-value-proc'] == Decimal('999999999999999.99')
    result = process_records(records, refs, START, END)
    assert result.metrics['uncertain'] == 1 and not result.selected


@pytest.mark.parametrize('identifier', [['543798-2026'], ' 543798-2026 '])
def test_equivalent_id_representations_cannot_bypass_dedup(notice, refs, identifier):
    notice['publication-number'] = identifier
    result = process_records([('p#0', notice), ('p#1', copy.deepcopy(notice))], refs, START, END)
    assert result.metrics['valid_unique'] == 1 and result.metrics['duplicates'] == 1
    assert result.metrics['duplicate_selected_ids'] == 0


@pytest.mark.parametrize('field,values', [
    ('publication-number', ['543798-2026', '543799-2026']),
    ('notice-type', ['cn-standard', 'cn-social']),
])
def test_mandatory_scalar_conflict_is_uncertain(notice, refs, field, values):
    notice[field] = values
    result = normalize(notice, refs, START, END)
    assert result.status == 'uncertain'
    assert result.reasons == ['CONFLICTING_SOURCE_VALUES']


@pytest.mark.parametrize('alter', ['date_start', 'latest', 'scope', 'token', 'fields'])
def test_inconsistent_manifest_is_rejected(tmp_path, notice, alter):
    run = tmp_path/'run'
    fetch_snapshot(run, END, session=Session([page([notice]), page([])]))
    manifest = read_json(run/'ted_raw.json')
    if alter == 'date_start':
        manifest['date_start'] = '2026-10-02'
    elif alter == 'latest':
        manifest['pages'][0]['request']['onlyLatestVersions'] = False
    elif alter == 'scope':
        manifest['pages'][0]['request']['scope'] = 'ACTIVE'
    elif alter == 'fields':
        manifest['pages'][0]['request']['fields'] = []
    else:
        manifest['pages'][1]['request']['iterationNextToken'] = 'broken'
    write_json(run/'ted_raw.json', manifest)
    with pytest.raises(ValueError):
        load_snapshot(run)


def test_old_processing_code_cannot_receive_current_test_pass(tmp_path, notice, monkeypatch):
    run, out = tmp_path/'run', tmp_path/'out'
    fetch_snapshot(run, END, session=Session([page([notice]), page([])]))
    process_snapshot(run, out)
    # Simulate package code changing after the delivery was produced.
    monkeypatch.setattr('ted_dataset.pipeline.processing_digest', lambda: 'new-code', raising=False)
    with pytest.raises(ValueError, match='Processing code'):
        update_report(run, out)
