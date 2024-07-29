# Prompts

## Prompt functions

The `template` decorator takes a function as an argument whose docstring is a Jinja template, and return a `Template` object:

```python
from prompts import template

@template
def few_shots(instructions, examples, question):
    """{{ instructions }}

    Examples
    --------
    {% for example in examples %}
    Q: {{ example.question }}
    A: {{ example.answer }}
    {% endfor %}
    Q: {{ question}}
    A: """
```

Caling the `Template` object renders the Jinja template:

```python
instructions = "Please answer the following question following the examples" examples = [
    {"question": "2+2=?", "answer":4},
    {"question": "3+3=?", "answer":6},
]
question = "4+4 = ?"

prompt = few_shots(instructions, examples, question)
```
