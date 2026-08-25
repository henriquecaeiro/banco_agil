import logging
from typing import Any, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

Intent = Literal["limit", "increase", "interview", "exchange", "end", "unsupported"]


class IntentResult(BaseModel):
    intent: Intent


def deterministic_intent(message: str) -> Intent:
    text = message.lower()
    if any(word in text for word in ("encerrar", "finalizar", "tchau", "obrigado", "era isso")):
        return "end"
    if any(word in text for word in ("câmbio", "cambio", "dólar", "dolar", "euro", "usd", "eur")):
        return "exchange"
    if "aumento" in text or "aumentar" in text:
        return "increase"
    if "limite" in text:
        return "limit"
    if "entrevista" in text:
        return "interview"
    return "unsupported"


class IntentService:
    """Uses Gemini only for language interpretation, with a local fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        structured_llm: Any | None = None,
    ):
        if structured_llm is not None:
            self.structured_llm = structured_llm
        elif api_key:
            llm = ChatGoogleGenerativeAI(model=model, api_key=api_key, temperature=0)
            self.structured_llm = llm.with_structured_output(IntentResult)
        else:
            self.structured_llm = None

    def classify(self, message: str) -> Intent:
        if self.structured_llm is None:
            return deterministic_intent(message)
        try:
            result = self.structured_llm.invoke(
                "Classifique a intenção do cliente bancário em exatamente uma categoria: "
                "limit (consultar limite), increase (aumentar limite), interview "
                "(entrevista financeira), exchange (cotação de moeda), end (encerrar) ou "
                f"unsupported. Mensagem: {message!r}"
            )
            parsed = (
                result if isinstance(result, IntentResult) else IntentResult.model_validate(result)
            )
            return parsed.intent
        # Provider/transport parsers expose multiple exception types; all must degrade locally.
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "LLM intent classification failed; using deterministic fallback: %s", error
            )
            return deterministic_intent(message)
