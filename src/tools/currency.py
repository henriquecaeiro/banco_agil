import re
from dataclasses import dataclass
from typing import ClassVar

from src.services.exchange_service import ExchangeService


@dataclass(frozen=True)
class CurrencyMatch:
    code: str
    display_name: str
    supported: bool


UNSUPPORTED_CURRENCY_ALIASES: ClassVar[dict[str, str]] = {
    "kwanza": "AOA",
    "kwanzas": "AOA",
    "aoa": "AOA",
    "canadense": "CAD",
    "cad": "CAD",
    "chf": "CHF",
    "suíço": "CHF",
    "suico": "CHF",
    "suíça": "CHF",
    "suica": "CHF",
    "franco": "CHF",
    "yuan": "CNY",
    "yuán": "CNY",
    "cny": "CNY",
    "won": "KRW",
    "krw": "KRW",
    "rupia": "INR",
    "rupias": "INR",
    "inr": "INR",
}

UNSUPPORTED_CURRENCY_PHRASES: ClassVar[tuple[tuple[str, str], ...]] = (
    ("dólar canadense", "CAD"),
    ("dolar canadense", "CAD"),
    ("franco suíço", "CHF"),
    ("franco suico", "CHF"),
)

SUPPORTED_CURRENCY_ALIASES: ClassVar[dict[str, str]] = {
    "dólar": "USD",
    "dolar": "USD",
    "usd": "USD",
    "euro": "EUR",
    "eur": "EUR",
    "libra": "GBP",
    "gbp": "GBP",
    "peso": "ARS",
    "ars": "ARS",
    "iene": "JPY",
    "jpy": "JPY",
}

CURRENCY_DISPLAY_NAMES: ClassVar[dict[str, str]] = {
    "USD": "dólar americano",
    "EUR": "euro",
    "GBP": "libra esterlina",
    "ARS": "peso argentino",
    "JPY": "iene japonês",
    "AOA": "kwanza",
    "CAD": "dólar canadense",
    "CHF": "franco suíço",
    "CNY": "yuan",
    "KRW": "won sul-coreano",
    "INR": "rupia indiana",
}

KNOWN_CURRENCY_CODES: ClassVar[frozenset[str]] = (
    ExchangeService.SUPPORTED_CURRENCIES
    | frozenset(CURRENCY_DISPLAY_NAMES)
    | frozenset(UNSUPPORTED_CURRENCY_ALIASES.values())
)


def identify_currency(message: str) -> CurrencyMatch | None:
    text = message.lower()

    for phrase, code in UNSUPPORTED_CURRENCY_PHRASES:
        if phrase in text:
            return _build_match(code, supported=False)

    for match in re.finditer(r"\b([a-z]{3})\b", text):
        code = match.group(1).upper()
        if ExchangeService.is_supported(code):
            return _build_match(code, supported=True)
        if code in KNOWN_CURRENCY_CODES:
            return _build_match(code, supported=False)

    words = set(re.findall(r"[a-zá-ú]+", text))

    for alias, code in UNSUPPORTED_CURRENCY_ALIASES.items():
        if alias in words:
            return _build_match(code, supported=False)

    for alias, code in SUPPORTED_CURRENCY_ALIASES.items():
        if alias in words:
            return _build_match(code, supported=True)

    return None


def _build_match(code: str, *, supported: bool) -> CurrencyMatch:
    return CurrencyMatch(
        code=code,
        display_name=CURRENCY_DISPLAY_NAMES.get(code, code),
        supported=supported,
    )


def unsupported_currency_message(match: CurrencyMatch) -> str:
    return (
        f"No momento não consigo consultar a cotação do {match.display_name} ({match.code}). "
        f"Posso consultar {ExchangeService.format_supported_currencies()}."
    )


def unidentified_currency_message() -> str:
    return (
        "Não consegui identificar qual moeda você deseja consultar. "
        f"Posso consultar {ExchangeService.format_supported_currencies()}."
    )
