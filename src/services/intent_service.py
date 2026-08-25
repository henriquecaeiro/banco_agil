import logging
from typing import Any, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from src.agents.decisions import AgentDecision, action_to_intent, intent_to_action
from src.agents.profiles import TRIAGE_PROFILE, AgentProfile

logger = logging.getLogger(__name__)

Intent = Literal["limit", "increase", "interview", "exchange", "end", "unsupported"]


class IntentResult(BaseModel):
    intent: Intent
    action: str | None = None
    currency: str | None = None


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


class AgentDecisionService:
    """Shared Gemini client that produces scoped agent decisions with deterministic fallback."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3.6-flash",
        structured_llm: Any | None = None,
        temperature: float = 0,
        timeout_seconds: float = 10,
        max_retries: int = 1,
    ):
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        if structured_llm is not None:
            self.structured_llm = structured_llm
        elif api_key:
            llm = ChatGoogleGenerativeAI(
                model=model,
                api_key=api_key,
                temperature=temperature,
                retries=max_retries,
                request_timeout=timeout_seconds,
            )
            self.structured_llm = llm.with_structured_output(IntentResult)
        else:
            self.structured_llm = None

    def decide(self, profile: AgentProfile, message: str) -> AgentDecision:
        fallback = AgentDecision(action=intent_to_action(deterministic_intent(message)))
        if fallback.action not in profile.allowed_actions:
            fallback = AgentDecision(action="unsupported")
        if self.structured_llm is None:
            return fallback
        try:
            result = self.structured_llm.invoke(profile.prompt(message))
            decision = self._parse_decision(result)
            if decision.action not in profile.allowed_actions:
                logger.warning(
                    "Rejected out-of-scope action %s for agent %s",
                    decision.action,
                    profile.name,
                )
                return fallback
            logger.info("Agent %s selected action %s", profile.name, decision.action)
            return decision
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "LLM agent decision failed for %s; using deterministic fallback: %s",
                profile.name,
                error,
            )
            return fallback

    def classify(self, message: str, profile: AgentProfile | None = None) -> Intent:
        decision = self.decide(profile or TRIAGE_PROFILE, message)
        return action_to_intent(decision.action)  # type: ignore[return-value]

    @staticmethod
    def _parse_decision(result: Any) -> AgentDecision:
        payload = result.get("parameters", result) if isinstance(result, dict) else result
        if isinstance(payload, AgentDecision):
            return payload
        if isinstance(payload, IntentResult):
            action = payload.action or intent_to_action(payload.intent)
            return AgentDecision(action=action, currency=payload.currency)
        if isinstance(payload, dict):
            if payload.get("action"):
                return AgentDecision.model_validate(payload)
            if payload.get("intent"):
                return AgentDecision(
                    action=intent_to_action(payload["intent"]),
                    currency=payload.get("currency"),
                )
        parsed = IntentResult.model_validate(payload)
        return AgentDecision(
            action=parsed.action or intent_to_action(parsed.intent),
            currency=parsed.currency,
        )


IntentService = AgentDecisionService
