import inspect
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Dict, Hashable, Optional

from jinja2 import Environment, StrictUndefined


@dataclass
class Template:
    """Represents a prompt template.

    A prompt template is a callable with renders the template returned by the
    function using the values that are passed to it. It is recommended to
    instantiate `Template` using the `template` decorator.

    >>> import prompts
    ...
    ... @prompts.template
    ... def prompt(name: str) -> str:
    ...    return "My name is {{name}}"

    It is not uncommon that, for the same taks, different models will perform
    better with different prompt. Here we thus allow to dispatch to associate a
    prompt with a task and dispatch the prompt based on the model being used; a
    `Template` instance is thus also a registry that associates model names to
    other templates.

    >>> @prompt.register("gpt2")
    ... def prompt_gpt2(name: str) -> str:
    ...     return "Hi GPT2! My name is {{name}}"

    The name of the model can then be passed to the render function along with
    the model name and the values of the arguments:

    >>> from prompts import render
    ...
    ... render(prompt, "gpt2", name="Dan")
    >>> "Hi GPT2! My name is Dan"

    Attributes
    ----------
    fn
        The function that returns a template.
    signature
        The function's signature.
    model
        The model the `Template` is associated with. Defaults to `None`.
    registry
        Registry that maps function names to their respective `Template`
        instances.

    """

    fn: Callable
    signature: inspect.Signature
    model: Optional[str] = None
    registry: Dict[str, Callable] = field(default_factory=dict)

    def __call__(self, *args, **kwargs) -> str:
        """Render and return the template.

        Returns
        -------
        The rendered template as a Python ``str``.

        """
        bound_arguments = self.signature.bind(*args, **kwargs)
        bound_arguments.apply_defaults()

        template = self.fn(**bound_arguments.arguments)

        return render(template, self.model, **bound_arguments.arguments)

    def __getitem__(self, model_name: str):
        """Get the prompt template corresponding to a model name.

        We return the default template when trying to fetch a
        template for a model that was not registered.

        Parameters
        ----------
        model_name
            The name of the model whose prompt template we want to retrieve.

        Returns
        -------
        The template registered for the model name.

        """
        try:
            return self.registry[model_name]
        except KeyError:
            self.model = model_name
            return self

    def register(self, model_name: str):
        """Register the prompt template, as represented by a prompt function,
        for a given model `model_name`.

        """

        def wrapper(fn: Callable):
            tpl = template(fn)
            tpl.model = model_name
            self.registry[model_name] = tpl
            return tpl

        return wrapper


def template(fn: Callable) -> Template:
    """Decorate a function that returns a prompt template.

    This allows to define prompts as the return value of a function and simplify
    their manipulation by providing some degree of encapsulation. It uses the
    `render` function internally to render templates.

    >>> import prompts
    >>>
    >>> @prompts.template
    >>> def build_prompt(question):
    ...    return "I have a {{question}}"
    ...
    >>> prompt = build_prompt("How are you?")

    This API can also be helpful in an "agent" context where parts of the prompt
    are set when the agent is initialized and never modified later. In this situation
    we can partially apply the prompt function at initialization.

    >>> import prompts
    ...
    >>> @prompts.template
    ... def solve_task(name: str, objective: str, task: str):
    ...     return '''Your name is {{name}}.
    ..      Your overall objective is to {{objective}}.
    ...     Please solve the following task: {{task}}'''
    ...
    >>> hal = ft.partial(solve_task, "HAL", "Travel to Jupiter")

    Returns
    -------
    A `Template` callable class which will render the template when called.

    """
    signature = inspect.signature(fn)

    return Template(fn, signature)


@lru_cache
def render(
    template: str,
    model_name: Optional[str] = None,
    **values: Optional[Dict[str, Hashable]],
) -> str:
    r"""Parse a Jinaj2 template and renders it using the passed values.

    This function removes extra whitespaces and linebreaks from templates to
    allow users to enter prompts more naturally than if they used Python's
    constructs directly. See the examples for a detailed explanation.

    Examples
    --------

    Outlines follow Jinja2's syntax

    >>> from prompts import render
    >>> render("I like {{food}} and {{sport}}", food="tomatoes", sport="tennis")
    I like tomatoes and tennis

    If the first line of the template is empty, `render` removes it

    >>> from prompts import render
    >>>
    >>> tpl = '''
    ... A new string'''
    >>> tpl
    ... '\nA new string'
    >>> render(tpl)
    ... 'a new string'

    Similarly, `render` ignores linebreaks introduced by placing the closing quotes
    underneath the text:

    >>> tpl = '''
    ... A new string
    ... '''
    >>> tpl
    ... '\nA new string\n'
    >>> render(tpl)
    ... 'A new string'

    If you want to insert a linebreak at the end of the rendered template, you will
    need to leave an empty line at the end of the template:

    >>> tpl = '''
    ... A new string
    ...
    ... '''
    >>> tpl
    ... '\nA new string\n\n'
    >>> render(tpl)
    ... 'A new string\n'

    `render` removes the identation in docstrings. This is particularly important
    when using prompt functions

    >>> tpl = '''
    ...    a string
    ...    and another string'''
    >>> tpl
    ... '\n   a string\n   and another string'
    >>> render(tpl)
    ... 'a string\nand another string'

    The indentation of the first line is assumed to be the same as the second line's

    >>> tpl = '''a string
    ...     and another'''
    >>> tpl
    ... 'a string\n    and another'
    >>> render(tpl)
    ... 'a string\nand another'

    To get a different indentation for the first and the second line, we can start the
    prompt on the string's second line:

    >>> tpl = '''
    ... First line
    ...   Second line'''
    >>> render(tpl)
    ... 'First Line\n  Second Line'

    Parameters
    ----------
    template
        A string that contains a template written with the Jinja2 syntax.
    model_name
        The name of the model to which the rendered string will be passed.
    **values
        Map from the variables in the template to their value.

    Returns
    -------
    A string that contains the rendered template.

    """
    # Dedent, and remove extra linebreak
    cleaned_template = inspect.cleandoc(template)

    # Add linebreak if there were any extra linebreaks that
    # `cleandoc` would have removed
    ends_with_linebreak = template.replace(" ", "").endswith("\n\n")
    if ends_with_linebreak:
        cleaned_template += "\n"

    # Remove extra whitespaces, except those that immediately follow a newline symbol.
    # This is necessary to avoid introducing whitespaces after backslash `\` characters
    # used to continue to the next line without linebreak.
    cleaned_template = re.sub(r"(?![\r\n])(\b\s+)", " ", cleaned_template)

    env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    jinja_template = env.from_string(cleaned_template)

    return jinja_template.render(**values)
