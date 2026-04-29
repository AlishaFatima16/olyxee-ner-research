import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from verification.normalizer import normalize_date


@pytest.mark.parametrize("text,expected", [
    ("March 2026", {"type": "date", "iso": "2026-03", "precision": "month"}),
    ("Mar 2026",   {"type": "date", "iso": "2026-03", "precision": "month"}),
    ("2017",       {"type": "date", "iso": "2017",    "precision": "year"}),
    ("Q1 2024",    {"type": "date", "iso": "2024-01", "precision": "quarter", "quarter": 1}),
    ("Q3 2025",    {"type": "date", "iso": "2025-07", "precision": "quarter", "quarter": 3}),
    ("FY2024",     {"type": "date", "iso": "2024",    "precision": "fiscal_year"}),
    ("FY 24",      {"type": "date", "iso": "2024",    "precision": "fiscal_year"}),
])
def test_date_formats(text, expected):
    assert normalize_date(text) == expected


def test_date_range():
    assert normalize_date("2018 - 2024") == {
        "type": "date_range",
        "start": "2018",
        "end": "2024",
        "precision": "year",
    }


def test_invalid_date():
    assert normalize_date("not a date at all") is None