from decimal import Decimal

from src.models import CreditInterview


def calculate_score(interview: CreditInterview) -> int:
    employment = {"formal": 300, "autônomo": 200, "desempregado": 0}
    dependents = (
        30
        if interview.numero_dependentes >= 3
        else {0: 100, 1: 80, 2: 60}[interview.numero_dependentes]
    )
    debts = -100 if interview.tem_dividas else 100
    score = (interview.renda_mensal / (interview.despesas_fixas_mensais + Decimal(1))) * 30
    return max(
        0, min(1000, round(float(score) + employment[interview.tipo_emprego] + dependents + debts))
    )
