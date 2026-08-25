from decimal import Decimal

import pytest

from src.tools.money import parse_money


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("R$ 1.000,00", Decimal("1000.00")),
        ("1000,50", Decimal("1000.50")),
        ("1000.50", Decimal("1000.50")),
        ("1.000", Decimal(1000)),
    ],
)
def test_parses_supported_money_formats(value: str, expected: Decimal) -> None:
    assert parse_money(value) == expected


@pytest.mark.parametrize("value", ["", "mil reais", "1,2,3"])
def test_rejects_invalid_money(value: str) -> None:
    with pytest.raises(ValueError):
        parse_money(value)
