from __future__ import annotations

import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_MONTHS = {
    "jan": "janeiro",
    "janeiro": "janeiro",
    "january": "janeiro",
    "fev": "fevereiro",
    "fevereiro": "fevereiro",
    "february": "fevereiro",
    "mar": "marco",
    "marco": "marco",
    "march": "marco",
    "abr": "abril",
    "abril": "abril",
    "april": "abril",
    "mai": "maio",
    "maio": "maio",
    "may": "maio",
    "jun": "junho",
    "junho": "junho",
    "june": "junho",
    "jul": "julho",
    "julho": "julho",
    "july": "julho",
    "ago": "agosto",
    "agosto": "agosto",
    "august": "agosto",
    "set": "setembro",
    "setembro": "setembro",
    "sep": "setembro",
    "september": "setembro",
    "out": "outubro",
    "outubro": "outubro",
    "oct": "outubro",
    "october": "outubro",
    "nov": "novembro",
    "novembro": "novembro",
    "november": "novembro",
    "dez": "dezembro",
    "dezembro": "dezembro",
    "dec": "dezembro",
    "december": "dezembro",
}


def normalize_reference_month(month: str) -> str:
    clean_month = " ".join(str(month).strip().split())
    if not clean_month:
        return ""

    normalized = _strip_accents(clean_month.lower())
    match = re.match(r"^([a-z]+)\s+de\s+(\d{4})$", normalized)
    if match:
        month_key, year = match.groups()
        month_name = _MONTHS.get(month_key, month_key)
        return f"{month_name} de {year}"

    slash_match = re.match(r"^([a-z]+)\s*/\s*(\d{4})$", normalized)
    if slash_match:
        month_key, year = slash_match.groups()
        month_name = _MONTHS.get(month_key, month_key)
        return f"{month_name} de {year}"

    return normalized


def format_brl(value: float | int | Decimal | str) -> str:
    amount = _parse_number(value)
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    sign = "-" if rounded < 0 else ""
    positive_amount = abs(rounded)
    integer_part = int(positive_amount)
    cents = int((positive_amount - integer_part) * 100)

    integer_str = f"{integer_part:,}".replace(",", ".")
    return f"{sign}R$ {integer_str},{cents:02d}"


def coalesce_price_display(
    price: str | None, fallback_value: float | int | Decimal | str | None
) -> str:
    if price and str(price).strip():
        return str(price).strip()

    if fallback_value is None:
        return "-"

    return format_brl(fallback_value)


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _parse_number(value: float | int | Decimal | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (float, int)):
        return Decimal(str(value))

    raw = value.strip()
    if raw.startswith("R$"):
        raw = raw[2:].strip()

    raw = raw.replace(".", "").replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation as error:
        raise ValueError(f"Cannot parse currency value: {value}") from error
