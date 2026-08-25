import httpx
import pytest

from src.agents.exchange_agent import ExchangeAgent
from src.services.exchange_service import ExchangeService


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def build_agent(handler) -> ExchangeAgent:
    service = ExchangeService("https://example.test", client(handler))
    return ExchangeAgent(service)


def test_quotes_supported_usd() -> None:
    agent = build_agent(lambda request: httpx.Response(200, json={"rates": {"BRL": 5.5}}))
    response = agent.respond("Quanto está o dólar?")

    assert "USD" in response
    assert "5.50" in response


def test_quotes_supported_eur() -> None:
    agent = build_agent(lambda request: httpx.Response(200, json={"rates": {"BRL": 6.1}}))
    response = agent.respond("Qual a cotação do euro?")

    assert "EUR" in response
    assert "6.10" in response


@pytest.mark.parametrize(
    ("message", "currency"),
    [
        ("Quanto está o dólar canadense?", "CAD"),
        ("Qual a cotação do CAD?", "CAD"),
        ("Quanto está o franco suíço?", "CHF"),
        ("Qual o valor do CHF?", "CHF"),
    ],
)
def test_unsupported_currency_lists_available_options(message: str, currency: str) -> None:
    called = {"count": 0}

    def fail_if_called(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(500)

    agent = build_agent(fail_if_called)
    response = agent.respond(message)

    assert called["count"] == 0
    assert currency in response
    assert "dólar americano (USD)" in response
    assert "euro (EUR)" in response
    assert "libra esterlina (GBP)" in response
    assert "peso argentino (ARS)" in response
    assert "iene japonês (JPY)" in response


def test_supported_currency_api_failure_uses_api_error_message() -> None:
    agent = build_agent(lambda request: httpx.Response(500))
    response = agent.respond("Quanto está o dólar?")

    assert "Não consegui consultar a cotação neste momento" in response
    assert "dólar americano (USD)" not in response


def test_missing_currency_prompts_user() -> None:
    agent = build_agent(lambda request: httpx.Response(200, json={"rates": {"BRL": 1.0}}))
    response = agent.respond("Quanto está a moeda?")

    assert "Informe a moeda" in response
