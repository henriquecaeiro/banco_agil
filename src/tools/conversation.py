def end_conversation(state: dict) -> dict:
    state["conversation_ended"] = True
    state["current_agent"] = None
    return state
