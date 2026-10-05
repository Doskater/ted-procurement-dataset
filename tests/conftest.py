import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def notice():
    """Real API record. Individual tests explicitly introduce synthetic defects."""
    data = json.loads((ROOT / "tests/fixtures/ted_sample_response.json").read_text())
    return copy.deepcopy(next(n for n in data["notices"] if n["publication-number"] == "543798-2026"))


@pytest.fixture
def refs():
    from ted_dataset.reference import load_reference
    return load_reference(ROOT / "data/reference")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import requests
    def blocked(*args, **kwargs):
        raise AssertionError("Tests must not access the network")
    monkeypatch.setattr(requests.sessions.Session, "request", blocked)
