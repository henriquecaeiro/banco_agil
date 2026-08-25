import httpx
import pytest

from src.services.exchange_service import ExchangeService


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_returns_valid_quote() -> None:
    service = ExchangeService(
        "https://example.test",
        client(lambda request: httpx.Response(200, json={"rates": {"BRL": 5.2}})),
    )
    assert service.quote_in_brl("USD") == 5.2


def test_handles_http_error() -> None:
    service = ExchangeService("https://example.test", client(lambda request: httpx.Response(500)))
    with pytest.raises(ConnectionError):
        service.quote_in_brl("USD")


def test_rejects_invalid_payload_and_currency() -> None:
    service = ExchangeService(
        "https://example.test", client(lambda request: httpx.Response(200, json={}))
    )
    with pytest.raises(TypeError):
        service.quote_in_brl("USD")
    with pytest.raises(ValueError):
        service.quote_in_brl("BTC")
