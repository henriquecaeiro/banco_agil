from src.services.intent_service import IntentService


class FakeStructuredLlm:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error

    def invoke(self, prompt: str):
        if self.error:
            raise self.error
        return self.result


def test_uses_structured_llm_for_natural_language() -> None:
    service = IntentService(structured_llm=FakeStructuredLlm({"intent": "increase"}))

    assert service.classify("queria ver se consigo um limite um pouco maior") == "increase"


def test_accepts_nested_structured_llm_payload() -> None:
    service = IntentService(
        structured_llm=FakeStructuredLlm({"parameters": {"intent": "exchange"}})
    )

    assert service.classify("qual moeda você recomenda?") == "exchange"


def test_falls_back_when_llm_is_not_configured() -> None:
    assert IntentService().classify("quanto está o euro?") == "exchange"


def test_routes_clear_increase_request_without_waiting_for_llm() -> None:
    service = IntentService(structured_llm=FakeStructuredLlm(error=TimeoutError("offline")))

    assert service.classify("será que dá pra subir um pouco meu limite?") == "increase"


def test_routes_clear_exchange_request_without_waiting_for_llm() -> None:
    service = IntentService(structured_llm=FakeStructuredLlm(error=TimeoutError("offline")))

    assert service.classify("quanto está o euro?") == "exchange"


def test_routes_supported_exchange_aliases_without_waiting_for_llm() -> None:
    service = IntentService(structured_llm=FakeStructuredLlm(error=TimeoutError("offline")))

    assert service.classify("qual a cotação da libra?") == "exchange"


def test_falls_back_when_llm_fails() -> None:
    service = IntentService(structured_llm=FakeStructuredLlm(error=TimeoutError("offline")))

    assert service.classify("quero consultar meu limite") == "limit"


def test_timeout_maps_natural_increase_to_request() -> None:
    service = IntentService(structured_llm=FakeStructuredLlm(error=TimeoutError("504")))

    assert service.classify("queria um limite um pouco maior") == "increase"


def test_timeout_maps_current_limit_question_to_consult() -> None:
    service = IntentService(structured_llm=FakeStructuredLlm(error=TimeoutError("504")))

    assert service.classify("quanto é meu limite?") == "limit"
