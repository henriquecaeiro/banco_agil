from typing import Literal

from pydantic import BaseModel, Field

AgentAction = Literal[
    "consult_limit",
    "request_increase",
    "start_interview",
    "continue_interview",
    "quote_exchange",
    "clarify_limit",
    "unsupported",
    "end",
]


class AgentDecision(BaseModel):
    action: AgentAction
    currency: str | None = Field(default=None)


INTENT_TO_ACTION: dict[str, AgentAction] = {
    "limit": "consult_limit",
    "increase": "request_increase",
    "interview": "start_interview",
    "exchange": "quote_exchange",
    "clarify_limit": "clarify_limit",
    "end": "end",
    "unsupported": "unsupported",
}

ACTION_TO_INTENT: dict[str, str] = {
    "consult_limit": "limit",
    "request_increase": "increase",
    "start_interview": "interview",
    "continue_interview": "unsupported",
    "quote_exchange": "exchange",
    "clarify_limit": "clarify_limit",
    "unsupported": "unsupported",
    "end": "end",
}


def action_to_intent(action: str) -> str:
    return ACTION_TO_INTENT.get(action, "unsupported")


def intent_to_action(intent: str) -> AgentAction:
    return INTENT_TO_ACTION.get(intent, "unsupported")
