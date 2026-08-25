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


def test_falls_back_when_llm_is_not_configured() -> None:
    assert IntentService().classify("quanto está o euro?") == "exchange"


def test_falls_back_when_llm_fails() -> None:
    service = IntentService(structured_llm=FakeStructuredLlm(error=TimeoutError("offline")))

    assert service.classify("quero consultar meu limite") == "limit"
