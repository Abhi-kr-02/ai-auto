def can_ai_reply(messages):
    if not messages:
        return True
    return messages[-1].direction == "inbound"
