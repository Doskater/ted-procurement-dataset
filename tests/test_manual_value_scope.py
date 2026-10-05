"""Regression from real manual QA: lot estimate is not a procedure estimate."""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from ted_dataset.normalize import normalize


def source_notice():
    return json.loads((Path(__file__).parent/'fixtures/notice_674236.json').read_text())['notice']


def test_real_manual_mismatch_has_explicit_procedure_scope(refs):
    notice = source_notice()
    assert 'estimated-value-proc' not in notice
    row = normalize(notice, refs, date(2026,8,6), date(2026,10,4)).row
    assert row['notice_id'] == '674236-2026' and row['lot_count'] == 1
    assert row['estimated_value'] is None and row['currency'] == ''
    assert row['qa_status'] == 'accepted'
    assert row['qa_note'] == 'MISSING_PROCEDURE_ESTIMATED_VALUE'


def test_single_lot_value_never_substitutes_for_procedure_value(refs):
    notice = source_notice()
    # Explicit synthetic enrichment: emulate a response containing lot fields.
    notice['estimated-value-lot'] = ['401698.90']
    notice['estimated-value-cur-lot'] = ['PLN']
    result = normalize(notice, refs, date(2026,8,6), date(2026,10,4))
    assert result.row['estimated_value'] is None and result.row['currency'] == ''
    notice['estimated-value-proc'] = '500000.00'
    notice['estimated-value-cur-proc'] = 'PLN'
    result = normalize(notice, refs, date(2026,8,6), date(2026,10,4))
    assert result.row['estimated_value'] == Decimal('500000.00')
    assert result.row['currency'] == 'PLN'
