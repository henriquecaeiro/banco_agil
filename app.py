import logging

import streamlit as st

from src.graph import BankingGraph

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Banco Ágil", page_icon="🏦")


def reset_service() -> None:
    st.session_state.graph = BankingGraph()
    st.session_state.state = {}
    st.session_state.history = [
        {
            "role": "assistant",
            "content": "Olá! Bem-vindo ao Banco Ágil. Para começarmos, poderia informar seu CPF?",
        }
    ]


if "graph" not in st.session_state:
    reset_service()

st.title("Banco Ágil")
st.caption("Atendimento demonstrativo para consultas de crédito e câmbio.")
with st.sidebar:
    st.subheader("Sessão")
    st.write("Encerrada" if st.session_state.state.get("conversation_ended") else "Em atendimento")
    st.caption("Use apenas os dados fictícios descritos no README.")
    if st.button("Reiniciar atendimento", use_container_width=True):
        reset_service()
        st.rerun()

for item in st.session_state.history:
    with st.chat_message(item["role"]):
        st.write(item["content"])

if prompt := st.chat_input("Digite sua mensagem"):
    st.session_state.history.append({"role": "user", "content": prompt})
    try:
        st.session_state.state = st.session_state.graph.invoke(st.session_state.state, prompt)
        response = st.session_state.state["response"]
    except (FileNotFoundError, KeyError, LookupError, OSError, TypeError, ValueError):
        logger.exception("Failed to process banking chat message")
        response = "Não consegui processar essa informação agora. Podemos tentar novamente?"
    st.session_state.history.append({"role": "assistant", "content": response})
    st.rerun()
