from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from typing_extensions import TypedDict


class Document(TypedDict):
    title: str
    text: str


class Role(Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


@dataclass
class Message:
    role: Role
    content: str


class Chat:
    def __init__(
        self,
        system_msg: Optional[str] = None,
        tools: Optional[List[BaseModel]] = None,
        documents: Optional[List[Document]] = None,
        history: List[Message] = [],
    ):
        self.history = history
        self.system = system_msg
        self.tools = tools
        self.documents = documents

    @property
    def trimmed_history(self):
        return self.history

    def __add__(self, other: Message):
        history = self.history
        history.append(other)
        return Chat(self.system, self.tools, self.documents, history=history)

    def __radd__(self, other: Message):
        history = self.history
        history.append(other)
        return Chat(self.system, self.tools, self.documents, history=history)

    def __iadd__(self, other: Message):
        self.history.append(other)
        return self

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.history[key]
        else:
            raise KeyError()

    def render(self, model_name: str):
        """Render the conversation using the model's chat template.

        TODO: Do this ourselves.

        Parameters
        ----------
        model_name
            The name of the model whose chat template we need to use.

        """
        from transformers import AutoTokenizer

        conversation = []
        if self.system is not None:
            conversation.append({"role": "system", "content": self.system})
        for message in self.trimmed_history:
            conversation.append({"role": message.role, "content": message.content})

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        return self.tokenizer.apply_chat_template(
            conversation, self.tools, self.documents
        )
