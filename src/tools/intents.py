from typing import Literal

Intent = Literal["limit", "increase", "interview", "exchange", "end", "unsupported"]


def deterministic_intent(message: str) -> Intent:
    text = message.lower()
    if any(
        word in text
        for word in ("encerrar", "finalizar", "tchau", "obrigado", "era isso", "deixa pra lá")
    ):
        return "end"
    if any(
        word in text
        for word in (
            "câmbio",
            "cambio",
            "cotação",
            "cotacao",
            "moeda",
            "dólar",
            "dolar",
            "canadense",
            "euro",
            "libra",
            "peso",
            "iene",
            "franco",
            "kwanza",
            "yuan",
            "won",
            "rupia",
            "usd",
            "eur",
            "gbp",
            "ars",
            "jpy",
            "cad",
            "chf",
            "aoa",
            "cny",
            "krw",
            "inr",
        )
    ):
        return "exchange"
    if any(
        phrase in text
        for phrase in ("aumento", "aumentar", "subir", "mais limite", "limite maior", "elevar")
    ):
        return "increase"
    if "limite" in text:
        return "limit"
    if "entrevista" in text:
        return "interview"
    return "unsupported"
