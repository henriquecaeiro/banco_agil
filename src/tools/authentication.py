import re
from datetime import date, datetime

from src.models import Customer


def normalize_cpf(cpf: str) -> str:
    return re.sub(r"\D", "", cpf)


def normalize_birth_date(value: str) -> str | None:
    value = value.strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return (
                date.fromisoformat(value).isoformat()
                if pattern == "%Y-%m-%d"
                else datetime.strptime(value, pattern).date().isoformat()
            )
        except ValueError:
            continue
    return None


def authenticate_customer(customer: Customer | None, birth_date: str) -> bool:
    normalized_date = normalize_birth_date(birth_date)
    return customer is not None and normalized_date == customer.data_nascimento
