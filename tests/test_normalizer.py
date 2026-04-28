import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alisha.normalizer import normalize_date, normalize_percent, normalize_money


def test_dates():
    assert normalize_date("March 2026") == "2026-03"
    assert normalize_date("2017") == "2017"
    assert normalize_date("2018 - 2024") == {"start": "2018", "end": "2024"}


def test_percent():
    assert normalize_percent("45%") == 0.45
    assert normalize_percent("over 65%") == 0.65


def test_money():
    assert normalize_money("$2.5M") == {"currency": "USD", "amount": 2_500_000}
    assert normalize_money("£500k") == {"currency": "GBP", "amount": 500_000}