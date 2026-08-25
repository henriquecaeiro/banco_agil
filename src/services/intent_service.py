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
    if any(word in text for word in ("encerrar", "finalizar", "tchau", "obrigado", "era isso", "deixa pra lá")):
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


class IntentService:
    """Uses Gemini only for language interpretation, with a local fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3.6-flash",
        structured_llm: Any | None = None,
    ):
        if structured_llm is not None:
            self.structured_llm = structured_llm
        elif api_key:
            llm = ChatGoogleGenerativeAI(
                model=model,
                api_key=api_key,
                temperature=0,
                retries=1,
                request_timeout=10,
            )
            self.structured_llm = llm.with_structured_output(IntentResult)
        else:
            self.structured_llm = None

    def classify(self, message: str) -> Intent:
        fallback = deterministic_intent(message)
        # Clear commands respond promptly; ambiguous requests for a larger limit still use Gemini.
        if self.structured_llm is None or self._is_clear_intent(message, fallback):
            return fallback
        try:
            result = self.structured_llm.invoke(
                "Classifique a intenção do cliente bancário em exatamente uma categoria: "
                "limit (consultar limite), increase (aumentar limite), interview "
                "(entrevista financeira), exchange (cotação de moeda), end (encerrar) ou "
                "unsupported. Use increase, e não limit, quando o cliente pedir para aumentar, "
                f"subir ou obter mais limite. Mensagem: {message!r}"
            )
            payload = result.get("parameters", result) if isinstance(result, dict) else result
            parsed = (
                payload
                if isinstance(payload, IntentResult)
                else IntentResult.model_validate(payload)
            )
            return parsed.intent
        # Provider/transport parsers expose multiple exception types; all must degrade locally.
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "LLM intent classification failed; using deterministic fallback: %s", error
            )
            return fallback

    @staticmethod
    def _is_clear_intent(message: str, intent: Intent) -> bool:
        if intent in {"end", "exchange", "increase", "interview"}:
            return True
        if intent != "limit":
            return False
        text = message.lower()
        return any(phrase in text for phrase in ("qual", "quanto", "consultar", "disponível"))
