from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Limits:
    begin: str = ""
    end: str = ""


@dataclass
class Special:
    sequence: Limits = Limits("", "")
    user: Limits = Limits("", "")
    assistant: Limits = Limits("", "")
    system: Limits = Limits("", "")


SPECIAL_TOKENS: Dict[Optional[str], Special] = {
    None: Special(),
    "google/gemma-2-9b": Special(Limits("<bos>", "<eos>")),
    "openai-community/gpt2": Special(Limits("", "<|endoftext|>")),
    "mistralai/Mistral-7B-v0.1": Special(Limits("<s>", "</s>")),
    "mistralai/Mistral-7B-Instruct-v0.1": Special(
        Limits("<s>", "</s>"),
        Limits("[INST]", "[/INST]"),
        Limits("", "</s>"),
    ),
}
