import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from verification.normalizer import normalize_money


@pytest.mark.parametrize("text,currency,amount,approximate", [
    ("$2.5M",          "USD", 2_500_000,    False),
    ("$1.2m",          "USD", 1_200_000,    False),
    ("£500k",          "GBP", 500_000,      False),
    ("€1.5bn",         "EUR", 1_500_000_000, False),
    ("₹50,000",        "INR", 50_000,       False),
    ("~$1M",           "USD", 1_000_000,    True),
    ("approx. £200k",  "GBP", 200_000,      True),
    ("1000 USD",       "USD", 1000,         False),
    ("-$500",          "USD", -500,         False),
])
def test_money_variants(text, currency, amount, approximate):
    result = normalize_money(text)
    assert result["currency"] == currency
    assert result["amount"] == amount
    assert result["approximate"] is approximate
    assert result["type"] == "money"


def test_invalid_money():
    assert normalize_money("not money") is None