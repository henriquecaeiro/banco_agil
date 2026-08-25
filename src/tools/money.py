from decimal import Decimal, InvalidOperation


def parse_money(value: str) -> Decimal:
    """Parse plain decimal values and common Brazilian currency formatting."""
    if not isinstance(value, str):
        raise TypeError("Informe um valor monetário válido.")
    normalized = value.strip().lower().replace("r$", "").replace(" ", "")
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif normalized.count(".") > 1:
        normalized = normalized.replace(".", "")
    elif normalized.count(".") == 1:
        whole, fraction = normalized.split(".")
        if len(fraction) == 3 and whole.lstrip("-").isdigit():
            normalized = whole + fraction
    try:
        return Decimal(normalized)
    except InvalidOperation as error:
        raise ValueError("Informe um valor monetário válido.") from error
