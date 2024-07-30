# Model-based prompt dispatching


Different models often require different prompts to achieve a given task. They are, in essence, not different prompts in the sense that they are supposed to perform the same operation. In the same way we use `functools.singledispatch` to dispatch a functionality on the type of the first
argument, it can be useful to dispatch the prompt on the model that is being used.

`prompts` provides a way to dispatch the prompt on the model:


```python
import prompts


@prompts.template
def a_simple_prompt(query: str):
    """<s>{{ query }}</s>"""

@a_simple_prompt.register("google/gemma-2-9b")
def a_simple_prompt_gemma(query: str):
    """<bos>{{ query }}<eos>"""
```

!!! note
    Choosing BOS and EOS based on the model is better achieved by using [special variables](special_tokens.md).
