OUT_OF_SCOPE_MESSAGE = (
    "Não consigo ajudar com esse assunto neste atendimento. "
    "Posso ajudar com consulta de limite, aumento de limite, entrevista financeira "
    "ou cotação das moedas disponíveis."
)

BANKING_UNAVAILABLE_MESSAGE = (
    "No momento não consigo realizar essa operação por aqui. "
    "Posso ajudar com consulta de limite, aumento de limite, entrevista financeira "
    "ou cotação das moedas disponíveis."
)

SYSTEM_QUESTION_MESSAGE = (
    "Sou o assistente do Banco Ágil. Posso ajudar com consulta de limite, "
    "aumento de limite, entrevista financeira ou cotação das moedas disponíveis."
)

AUTH_REQUIRED_MESSAGE = (
    "Antes de continuarmos, preciso confirmar sua identidade. Por favor, informe seu CPF."
)

AUTH_BIRTH_DATE_MESSAGE = (
    "Para continuar, informe sua data de nascimento no formato DD/MM/AAAA."
)

CAPABILITIES_MESSAGE = (
    "Posso ajudar com limite de crédito, aumento de limite, entrevista financeira ou câmbio."
)

BANKING_OUT_OF_SCOPE_KEYWORDS = (
    "pix",
    "empréstimo",
    "emprestimo",
    "abrir uma conta",
    "cancelar minha conta",
    "financiar",
    "cartão",
    "cartao",
    "investimento",
    "bloquear meu cartão",
)

SYSTEM_QUESTION_KEYWORDS = (
    "gemini",
    "langgraph",
    "prompt",
    "node",
    "agente está falando",
    "instruções internas",
    "clientes.csv",
)


def unsupported_intent_message(message: str) -> str:
    text = message.lower()
    if any(keyword in text for keyword in SYSTEM_QUESTION_KEYWORDS):
        return SYSTEM_QUESTION_MESSAGE
    if any(keyword in text for keyword in BANKING_OUT_OF_SCOPE_KEYWORDS):
        return BANKING_UNAVAILABLE_MESSAGE
    return OUT_OF_SCOPE_MESSAGE
