# Handle special tokens

Tokens that indicate the beginnning of a sequence, an end of sequence, that
delineate user and assistant turns in a conversation, etc. are model-specific.
This means that one needs to write a new prompt each time they use a new model,
only replacing these special tokens. This is error-prone and leads to duplicated
work.

`prompts` provides special variables in its templates that allows user to use special tokens in their prompts in a model-agnotic way:

```python
import prompts


@prompts.template
def a_simple_prompt(query: str):
    """{{ bos + query + eos }}"""


print(a_simple_prompt["mistralai/Mistral-7B-v0.1"]("question"))
# <s>question</s>

print(a_simple_prompt["google/gemma-2-9b"]("question"))
# <bos>question<eos>
```


!!! note "Registry"

    The registry is currently limited to a few models. Please [open an issue](https://github.com/outlines-dev/prompts/issues) if you
    want to use `prompts` with a model that is not currently in the registry.
