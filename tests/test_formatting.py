from decimal import Decimal

import pytest

from src.utils.formatting import coalesce_price_display, format_brl, normalize_reference_month


def test_normalize_reference_month_keeps_consistent_format() -> None:
    assert normalize_reference_month("Abril de 2024") == "abril de 2024"
    assert normalize_reference_month("marco/2025") == "marco de 2025"


def test_normalize_reference_month_returns_empty_for_blank_values() -> None:
    assert normalize_reference_month("  ") == ""


def test_format_brl_with_numeric_values() -> None:
    assert format_brl(12345.5) == "R$ 12.345,50"
    assert format_brl(Decimal("0")) == "R$ 0,00"


def test_coalesce_price_display_prefers_api_price() -> None:
    assert coalesce_price_display("R$ 10.000,00", 10000) == "R$ 10.000,00"


def test_coalesce_price_display_uses_fallback_value() -> None:
    assert coalesce_price_display("", 10000) == "R$ 10.000,00"


def test_format_brl_raises_for_invalid_input() -> None:
    with pytest.raises(ValueError):
        format_brl("abc")
