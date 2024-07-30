from prompts.tokens import Special


def test_simple():
    special = Special()
    assert special.assistant.begin == ""
