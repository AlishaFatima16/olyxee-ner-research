import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from verification.normalizer import normalize_percent


@pytest.mark.parametrize("text,value,approximate", [
    ("45%",            0.45, False),
    ("over 65%",       0.65, True),
    ("more than 50%",  0.50, True),
    ("~20%",           0.20, True),
    ("approx. 30%",    0.30, True),
    ("about 12.5%",    0.125, True),
    ("-5%",           -0.05, False),
])
def test_percent_variants(text, value, approximate):
    result = normalize_percent(text)
    assert result["value"] == value
    assert result["approximate"] is approximate
    assert result["type"] == "percentage"


def test_invalid_percent():
    assert normalize_percent("no percent here") is None