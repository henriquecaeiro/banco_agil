import logging

import streamlit as st

from src.graph import BankingGraph
from src.ui.chat_processing import (
    process_chat_turn,
    resolve_loading_message,
    run_with_processing_flag,
)

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Banco Ágil", page_icon="🏦")


def reset_service() -> None:
    st.session_state.graph = BankingGraph()
    st.session_state.state = {}
    st.session_state.processing = False
    st.session_state.history = [
        {
            "role": "assistant",
            "content": "Olá! Bem-vindo ao Banco Ágil. Para começarmos, poderia informar seu CPF?",
        }
    ]


if "graph" not in st.session_state:
    reset_service()

if "processing" not in st.session_state:
    st.session_state.processing = False

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

prompt = st.chat_input(
    "Digite sua mensagem",
    disabled=st.session_state.processing,
)

if prompt and not st.session_state.processing:
    st.session_state.history.append({"role": "user", "content": prompt})
    loading_message = resolve_loading_message(st.session_state.state, prompt)

    def handle_turn() -> None:
        with st.spinner(loading_message):
            updated_state, response = process_chat_turn(
                st.session_state.graph,
                st.session_state.state,
                prompt,
            )
            st.session_state.state = updated_state
            st.session_state.history.append({"role": "assistant", "content": response})

    run_with_processing_flag(
        lambda value: st.session_state.__setitem__("processing", value),
        handle_turn,
    )
    st.rerun()
