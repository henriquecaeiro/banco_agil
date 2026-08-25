from typing import Any, TypedDict


class BankingState(TypedDict, total=False):
    message: str
    messages: list[dict[str, str]]
    authenticated: bool
    authentication_attempts: int
    customer: dict[str, Any]
    current_agent: str | None
    intent: str | None
    conversation_ended: bool
    pending_auth_cpf: str
    pending_credit_request: dict[str, Any] | None
    suggested_currency: str
    credit_interview: dict[str, Any]
    response: str
