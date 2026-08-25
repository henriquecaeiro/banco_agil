import re
from datetime import date

from src.models import Customer


def normalize_cpf(cpf: str) -> str:
    return re.sub(r"\D", "", cpf)


def normalize_birth_date(value: str) -> str | None:
    value = value.strip()
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        pass
    try:
        day, month, year = (int(part) for part in value.split("/"))
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def authenticate_customer(customer: Customer | None, birth_date: str) -> bool:
    normalized_date = normalize_birth_date(birth_date)
    return customer is not None and normalized_date == customer.data_nascimento
