<div align="center" style="margin-bottom: 1em;">

<img src="./docs/assets/images/logo.png" alt="Prompts Logo" width=500></img>

[![.txt Twitter][dottxt-twitter-badge]][dottxt-twitter]

[![Contributors][contributors-badge]][contributors]
[![Discord][discord-badge]][discord]


*A prompting library.*

Made with ❤👷️ by the team at [.txt](https://dottxt.co).

</div>


## Prompt functions

The `template` decorator takes a function as an argument whose docstring is a Jinja template, and returns a `Template` object:

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

Calling the `Template` object renders the Jinja template:

```python
instructions = "Please answer the following question following the examples" examples = [
    {"question": "2+2=?", "answer":4},
    {"question": "3+3=?", "answer":6},
]
question = "4+4 = ?"

prompt = few_shots(instructions, examples, question)
```


[contributors]: https://github.com/dottxt-ai/prompts/graphs/contributors
[contributors-badge]: https://img.shields.io/github/contributors/dottxt-ai/prompts?style=flat-square&logo=github&logoColor=white&color=ECEFF4
[dottxt-twitter]: https://twitter.com/dottxtai
[discord]: https://discord.gg/R9DSu34mGd
[discord-badge]: https://img.shields.io/discord/1182316225284554793?color=81A1C1&logo=discord&logoColor=white&style=flat-square
[dottxt-twitter-badge]: https://img.shields.io/twitter/follow/dottxtai?style=social
