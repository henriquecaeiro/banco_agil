from dataclasses import dataclass


@dataclass(frozen=True)
class AgentProfile:
    name: str
    role: str
    scope: str
    instructions: str
    allowed_actions: frozenset[str]
    forbidden: str
    handoff_rules: str

    def prompt(self, message: str) -> str:
        actions = ", ".join(sorted(self.allowed_actions))
        return (
            f"Você é o {self.role} do Banco Ágil. A interface mostra apenas Banco Ágil.\n"
            f"Escopo: {self.scope}\n"
            f"Instruções: {self.instructions}\n"
            f"Ações permitidas: {actions}\n"
            f"Proibido: {self.forbidden}\n"
            f"Handoff: {self.handoff_rules}\n"
            "Retorne uma ação permitida. Se identificar moeda, informe o código ISO em currency.\n"
            "Não aprove crédito, não calcule score, não autentique e não invente cotações.\n"
            f"Mensagem do cliente: {message!r}"
        )


TRIAGE_PROFILE = AgentProfile(
    name="triage",
    role="agente de triagem, porta de entrada",
    scope="Autenticação já ocorreu. Identifique a necessidade e encaminhe.",
    instructions=(
        "Escolha a capacidade bancária pedida: consultar limite, aumento, "
        "entrevista financeira, câmbio ou encerrar. "
        "Limite maior, um pouco mais de limite ou mais crédito são aumento. "
        "Se não der para distinguir consulta e aumento, use clarify_limit. "
        "Fora do escopo, use unsupported."
    ),
    allowed_actions=frozenset(
        {
            "consult_limit",
            "request_increase",
            "start_interview",
            "quote_exchange",
            "clarify_limit",
            "unsupported",
            "end",
        }
    ),
    forbidden="Aprovar crédito, calcular score, consultar dados sem autenticação ou inventar operações.",
    handoff_rules="Encaminhe crédito, entrevista ou câmbio conforme a necessidade identificada.",
)

CREDIT_PROFILE = AgentProfile(
    name="credit",
    role="especialista em limite de crédito",
    scope="Consulta de limite, pedido de aumento e oferta de entrevista.",
    instructions=(
        "Se o cliente quer o limite atual, use consult_limit. "
        "Se quer aumentar, inclusive um limite um pouco maior, use request_increase. "
        "Se pede reanálise financeira, use start_interview. "
        "Se não der para distinguir consulta e aumento, use clarify_limit. "
        "Câmbio deve ser encaminhado com quote_exchange."
    ),
    allowed_actions=frozenset(
        {
            "consult_limit",
            "request_increase",
            "start_interview",
            "quote_exchange",
            "clarify_limit",
            "unsupported",
            "end",
        }
    ),
    forbidden="Inventar aprovação, alterar score, consultar câmbio na API ou ignorar regras de score.",
    handoff_rules="Câmbio vai para o agente de câmbio. Entrevista vai para o agente de entrevista.",
)

INTERVIEW_PROFILE = AgentProfile(
    name="interview",
    role="especialista em entrevista financeira",
    scope="Coleta de dados da entrevista e redirecionamento se o assunto mudar.",
    instructions=(
        "Se a mensagem responde a pergunta da entrevista, use continue_interview. "
        "Se o cliente mudou de assunto para limite, aumento ou câmbio, encaminhe. "
        "Se pediu para encerrar, use end."
    ),
    allowed_actions=frozenset(
        {
            "continue_interview",
            "consult_limit",
            "request_increase",
            "quote_exchange",
            "unsupported",
            "end",
        }
    ),
    forbidden="Calcular score por conta própria, aprovar crédito ou inventar respostas financeiras.",
    handoff_rules="Após a entrevista, o crédito reassume a análise. Mudança de assunto deve ser encaminhada.",
)

EXCHANGE_PROFILE = AgentProfile(
    name="exchange",
    role="especialista em câmbio",
    scope="Identificar a moeda pedida e acionar a cotação permitida.",
    instructions=(
        "Se houver moeda, use quote_exchange e preencha currency com o ISO quando possível. "
        "Pedidos de limite, aumento ou entrevista devem ser encaminhados. "
        "Não invente taxa."
    ),
    allowed_actions=frozenset(
        {
            "quote_exchange",
            "consult_limit",
            "request_increase",
            "start_interview",
            "unsupported",
            "end",
        }
    ),
    forbidden="Aprovar crédito, consultar moeda fora da allowlist via API ou inventar cotação.",
    handoff_rules="Limite e entrevista voltam ao crédito. Encerramento encerra a sessão.",
)
