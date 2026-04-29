import re
import dateparser

CURRENCY_SYMBOLS = {"$": "USD", "£": "GBP", "€": "EUR", "₹": "INR"}
MULTIPLIERS = {"k": 1_000, "m": 1_000_000, "bn": 1_000_000_000, "b": 1_000_000_000}
APPROX_MARKERS = r"(~|≈|approx\.?|about|around|over|under|more than|less than)"


def normalize_date(text: str):
    text = text.strip()

    # Range: "2018 - 2024"
    range_match = re.match(r"^\s*(\d{4})\s*[-–]\s*(\d{4})\s*$", text)
    if range_match:
        return {
            "type": "date_range",
            "start": range_match.group(1),
            "end": range_match.group(2),
            "precision": "year",
        }

    # Quarter: "Q1 2024", "Q3 2025"
    q_match = re.match(r"^\s*Q([1-4])\s+(\d{4})\s*$", text, flags=re.IGNORECASE)
    if q_match:
        quarter, year = q_match.groups()
        month = (int(quarter) - 1) * 3 + 1
        return {
            "type": "date",
            "iso": f"{year}-{month:02d}",
            "precision": "quarter",
            "quarter": int(quarter),
        }

    # Fiscal year: "FY2024", "FY 24"
    fy_match = re.match(r"^\s*FY\s*(\d{2,4})\s*$", text, flags=re.IGNORECASE)
    if fy_match:
        year = fy_match.group(1)
        if len(year) == 2:
            year = "20" + year
        return {"type": "date", "iso": year, "precision": "fiscal_year"}

    parsed = dateparser.parse(text, settings={"PREFER_DAY_OF_MONTH": "first"})
    if not parsed:
        return None

    # Year only: "2017"
    if re.fullmatch(r"\d{4}", text):
        return {"type": "date", "iso": parsed.strftime("%Y"), "precision": "year"}
    # Month + year: "March 2026"
    if not re.search(r"\b\d{1,2}(st|nd|rd|th)?\b", text.lower()):
        return {"type": "date", "iso": parsed.strftime("%Y-%m"), "precision": "month"}
    # Full date
    return {"type": "date", "iso": parsed.strftime("%Y-%m-%d"), "precision": "day"}


def normalize_percent(text: str):
    is_approx = bool(re.search(APPROX_MARKERS, text, flags=re.IGNORECASE))
    cleaned = re.sub(APPROX_MARKERS, "", text, flags=re.IGNORECASE).strip()

    match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", cleaned)
    if not match:
        return None

    return {
        "type": "percentage",
        "value": round(float(match.group(1)) / 100, 4),
        "approximate": is_approx,
    }


def normalize_money(text: str):
    cleaned = text.strip().replace(",", "")

    is_approx = bool(re.match(r"^(~|≈|approx\.?|about|around)", cleaned, flags=re.IGNORECASE))
    cleaned = re.sub(r"^(~|≈|approx\.?|about|around)\s*", "", cleaned, flags=re.IGNORECASE)

    # Handle leading minus before currency symbol: "-$500"
    is_negative = False
    if cleaned.startswith("-"):
        is_negative = True
        cleaned = cleaned[1:].strip()

    match = re.match(
        r"^\s*([\$£€₹])?\s*(-?\d+(?:\.\d+)?)\s*(bn|b|m|k)?\s*(USD|EUR|GBP|INR)?\s*$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    symbol, number, suffix, code = match.groups()
    amount = float(number)
    if suffix:
        amount *= MULTIPLIERS[suffix.lower()]
    if is_negative:
        amount = -amount
    if amount.is_integer():
        amount = int(amount)

    currency = code.upper() if code else CURRENCY_SYMBOLS.get(symbol, "USD")
    return {
        "type": "money",
        "currency": currency,
        "amount": amount,
        "approximate": is_approx,
    }

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