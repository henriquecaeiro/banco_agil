from decimal import Decimal

import pytest

from src.tools.money import parse_money


@pytest.mark.parametrize(
    "value",
    [
        "150000",
        "150000.00",
        "150000,00",
        "R$ 150000",
        "R$150000",
        "150.000",
        "150.000,00",
        "R$ 150.000",
        "R$150.000",
        "R$ 150.000,00",
        "R$150.000,00",
    ],
)
def test_parses_equivalent_credit_amount_formats(value: str) -> None:
    assert parse_money(value) == Decimal(150000)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1000,50", Decimal("1000.50")),
        ("1000.50", Decimal("1000.50")),
        ("150.000,50", Decimal("150000.50")),
        ("150000.50", Decimal("150000.50")),
    ],
)
def test_preserves_decimal_portion_across_supported_locales(
    value: str, expected: Decimal
) -> None:
    assert parse_money(value) == expected


@pytest.mark.parametrize("value", ["banana", "R$ abc", "", "R$", "mil reais", "1,2,3"])
def test_rejects_invalid_money_syntax(value: str) -> None:
    with pytest.raises(ValueError):
        parse_money(value)
