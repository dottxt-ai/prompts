from prompts.chat import Chat, Message


def test_simple():
    chat = Chat("system message")
    new_chat = chat + Message("user", "new user message")
    new_chat += Message("assistant", "new assistant message")
