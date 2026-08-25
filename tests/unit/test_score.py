from decimal import Decimal

import pytest

from src.models import CreditInterview
from src.tools.score import calculate_score


@pytest.mark.parametrize(
    ("employment", "dependents", "debts"),
    [("formal", 0, False), ("autônomo", 1, True), ("desempregado", 2, False), ("formal", 3, True)],
)
def test_score_uses_all_interview_factors(employment: str, dependents: int, debts: bool) -> None:
    score = calculate_score(
        CreditInterview(
            renda_mensal=Decimal(3000),
            tipo_emprego=employment,
            despesas_fixas_mensais=Decimal(1000),
            numero_dependentes=dependents,
            tem_dividas=debts,
        )
    )
    assert 0 <= score <= 1000


def test_score_is_clamped() -> None:
    high = CreditInterview(
        renda_mensal=Decimal(999999),
        tipo_emprego="formal",
        despesas_fixas_mensais=Decimal(0),
        numero_dependentes=0,
        tem_dividas=False,
    )
    assert calculate_score(high) == 1000
