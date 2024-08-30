# Handle special tokens

Tokens that indicate the beginning of a sequence, an end of sequence, that
delineate user and assistant turns in a conversation, etc. are model-specific.
This means that one needs to write a new prompt each time they use a new model,
only replacing these special tokens. This is error-prone and leads to duplicated
work.


## Beginning and end of sequences

`prompts` provides special variables in its templates that allows user to use special tokens in their prompts in a model-agnostic way:

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


## Chat and Instruct models

`prompts` also provides special variables `user`, `assistant` and `system` that are related to chat workflows, so you can design prompts with a chat format in a model-agnostic way:

```python
import prompts


@prompts.template
def simple_prompt(favorite: str):
    """{{ bos + user.begin}} What is your favorite {{favorite + '? ' + user.end}}
    {{ assistant.begin }}
    """
```

Chat templates are so idiosyncratic, however, that we recommend using the `Chat` class to format according to chat templates.
