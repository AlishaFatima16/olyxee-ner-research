import re
import dateparser

CURRENCY_SYMBOLS = {"$": "USD", "£": "GBP", "€": "EUR", "₹": "INR"}
MULTIPLIERS = {"k": 1_000, "m": 1_000_000, "bn": 1_000_000_000, "b": 1_000_000_000}


def normalize_date(text: str):
    range_match = re.match(r"^\s*(\d{4})\s*[-–]\s*(\d{4})\s*$", text)
    if range_match:
        return {"start": range_match.group(1), "end": range_match.group(2)}

    parsed = dateparser.parse(text, settings={"PREFER_DAY_OF_MONTH": "first"})
    if not parsed:
        return None

    if re.fullmatch(r"\d{4}", text.strip()):
        return parsed.strftime("%Y")
    if not re.search(r"\b\d{1,2}(st|nd|rd|th)?\b", text.lower()):
        return parsed.strftime("%Y-%m")
    return parsed.strftime("%Y-%m-%d")


def normalize_percent(text: str):
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if not match:
        return None
    return round(float(match.group(1)) / 100, 4)


def normalize_money(text: str):
    cleaned = text.strip().replace(",", "")
    match = re.match(
        r"^\s*([\$£€₹])?\s*(\d+(?:\.\d+)?)\s*(bn|b|m|k)?\s*(USD|EUR|GBP|INR)?\s*$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    symbol, number, suffix, code = match.groups()
    amount = float(number)
    if suffix:
        amount *= MULTIPLIERS[suffix.lower()]

    currency = code.upper() if code else CURRENCY_SYMBOLS.get(symbol, "USD")
    return {"currency": currency, "amount": amount}


def normalize_entity(label: str, text: str):
    """Route an entity to the right normalizer. Returns None if no rule matches."""
    label = label.upper()
    if label == "DATE":
        return normalize_date(text)
    if label in {"PERCENT", "PERCENTAGE"}:
        return normalize_percent(text)
    if label in {"MONEY", "AMOUNT"}:
        return normalize_money(text)
    return None