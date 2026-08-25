import logging
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

DEFAULT_LOADING_MESSAGE = "Verificando as informações..."
GENERIC_ERROR_MESSAGE = "Não consegui processar essa informação agora. Podemos tentar novamente?"

T = TypeVar("T")


def resolve_loading_message(state: dict, prompt: str) -> str:
    if not state.get("authenticated"):
        return "Verificando seus dados..."

    current_agent = state.get("current_agent")
    if current_agent == "awaiting_limit":
        return "Analisando sua solicitação..."
    if current_agent == "interview":
        return "Atualizando sua análise de crédito..."

    text = prompt.lower()
    exchange_terms = (
        "câmbio",
        "cambio",
        "cotação",
        "cotacao",
        "dólar",
        "dolar",
        "euro",
        "libra",
        "peso",
        "iene",
    )
    if any(term in text for term in exchange_terms):
        return "Consultando a cotação..."

    return DEFAULT_LOADING_MESSAGE


def process_chat_turn(graph, state: dict, prompt: str) -> tuple[dict, str]:
    try:
        updated_state = graph.invoke(state, prompt)
        return updated_state, updated_state["response"]
    except (FileNotFoundError, KeyError, LookupError, OSError, TypeError, ValueError):
        logger.exception("Failed to process banking chat message")
        return state, GENERIC_ERROR_MESSAGE


def run_with_processing_flag(set_processing: Callable[[bool], None], operation: Callable[[], T]) -> T:
    set_processing(True)
    try:
        return operation()
    finally:
        set_processing(False)
