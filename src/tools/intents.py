from typing import Literal

Intent = Literal[
    "limit",
    "increase",
    "interview",
    "exchange",
    "end",
    "unsupported",
    "clarify_limit",
]


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
        for phrase in (
            "aumento",
            "aumentar",
            "subir",
            "elevar",
            "mais limite",
            "mais crédito",
            "mais credito",
            "mais de limite",
            "um pouco mais",
            "limite maior",
            "limite fosse maior",
            "um pouco maior",
        )
    ):
        return "increase"
    if any(phrase in text for phrase in ("o banco libera", "banco libera pra")):
        return "limit"
    mentions_credit = any(word in text for word in ("limite", "crédito", "credito"))
    if mentions_credit:
        if "maior" in text:
            return "increase"
        if any(word in text for word in ("quanto", "qual", "consultar", "consulta")):
            return "limit"
        return "clarify_limit"
    if "entrevista" in text:
        return "interview"
    return "unsupported"
