from decimal import Decimal

import pytest

from src.models import CreditInterview
from src.tools.score import calculate_score


@pytest.mark.parametrize(
    ("employment", "dependents", "debts", "expected"),
    [
        ("formal", 0, False, 590),
        ("autônomo", 1, True, 270),
        ("desempregado", 2, False, 250),
        ("formal", 3, True, 320),
    ],
)
def test_score_uses_all_interview_factors(
    employment: str, dependents: int, debts: bool, expected: int
) -> None:
    score = calculate_score(
        CreditInterview(
            renda_mensal=Decimal(3000),
            tipo_emprego=employment,
            despesas_fixas_mensais=Decimal(1000),
            numero_dependentes=dependents,
            tem_dividas=debts,
        )
    )
    assert score == expected


def test_score_is_clamped() -> None:
    high = CreditInterview(
        renda_mensal=Decimal(999999),
        tipo_emprego="formal",
        despesas_fixas_mensais=Decimal(0),
        numero_dependentes=0,
        tem_dividas=False,
    )
    assert calculate_score(high) == 1000


def test_score_is_clamped_to_minimum() -> None:
    low = CreditInterview(
        renda_mensal=Decimal(0),
        tipo_emprego="desempregado",
        despesas_fixas_mensais=Decimal(1000),
        numero_dependentes=3,
        tem_dividas=True,
    )
    assert calculate_score(low) == 0
