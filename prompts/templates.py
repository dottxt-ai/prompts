import inspect
import re
import warnings
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Dict, Hashable, Optional, cast

from jinja2 import Environment, StrictUndefined

from prompts.tokens import SPECIAL_TOKENS, Special


@dataclass
class Template:
    """Represents a prompt template.

    A prompt template is a callable that, given a Jinja2 template and a set of values,
    renders the template using those values. It is recommended to instantiate `Temaplate`
    using the `template` decorator, which extracts the template from the function's
    docstring and its variables from the function's signature.

    It is not uncommon that, for the same taks, different models will perform
    better with different prompt. Here we thus allow to dispatch to associate a
    prompt with a task and dispatch the prompt based on the model being used; a
    `Template` instance is thus also a registry that associates model names to
    other templates.


    Attributes
    ----------
    template
        The template to render.
    signature
        The prompt function's signature.
    model
        The model the `Template` is associated with. Defaults to `None`.
    registry
        Registry that maps function names to their respective `Template`
        instances.

    """

    template: str
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
        return render(self.template, self.model, **bound_arguments.arguments)

    def __str__(self):
        return self.template

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
        for the model name.

        """

        def wrapper(fn: Callable):
            tpl = template(fn)
            tpl.model = model_name
            self.registry[model_name] = tpl
            return tpl

        return wrapper


def template(fn: Callable) -> Template:
    """Decorate a function that contains a prompt template.

    This allows to define prompts in the docstring of a function and simplify their
    manipulation by providing some degree of encapsulation. It uses the `render`
    function internally to render templates.

    >>> import outlines
    >>>
    >>> @outlines.prompt
    >>> def build_prompt(question):
    ...    "I have a ${question}"
    ...
    >>> prompt = build_prompt("How are you?")

    This API can also be helpful in an "agent" context where parts of the prompt
    are set when the agent is initialized and never modified later. In this situation
    we can partially apply the prompt function at initialization.

    >>> import outlines
    >>> import functools as ft
    ...
    >>> @outlines.prompt
    ... def solve_task(name: str, objective: str, task: str):
    ...     '''Your name is {{name}}.
    ..      Your overall objective is to {{objective}}.
    ...     Please solve the following task: {{task}}'''
    ...
    >>> hal = ft.partial(solve_task, "HAL", "Travel to Jupiter")

    Returns
    -------
    A `Prompt` callable class which will render the template when called.

    """
    signature = inspect.signature(fn)

    # The docstring contains the template that will be rendered to be used
    # as a prompt to the language model.
    docstring = fn.__doc__
    if docstring is None:
        raise TypeError("Could not find a template in the function's docstring.")

    template = cast(str, docstring)

    return Template(template, signature)


@lru_cache
def render(
    template: str,
    model_name: Optional[str] = None,
    **values: Optional[Dict[str, Hashable]],
) -> str:
    r"""Parse a Jinaj2 template and translate it into an Outlines graph.

    This function removes extra whitespaces and linebreaks from templates to
    allow users to enter prompts more naturally than if they used Python's
    constructs directly. See the examples for a detailed explanation.

    We also define the `bos` and `eos` special variables which, when used, will
    be replaced by the model's BOS and EOS tokens respectively. This allows you
    to write prompts that are model-agnostic.

    Examples
    --------

    Outlines follow Jinja2's syntax

    >>> import outlines
    >>> outline = outlines.render("I like {{food}} and {{sport}}", food="tomatoes", sport="tennis")
    I like tomatoes and tennis

    If the first line of the template is empty, `render` removes it

    >>> from outlines import render
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

    # Warn the user when the model is not present in the special token registry
    if model_name not in SPECIAL_TOKENS:
        warnings.warn(
            UserWarning(
                f"The model {model_name} is not present in the special token registry."
                "As a result, EOS and BOS tokens will be rendered as the empty string."
                "Please open an issue: https://github.com/outlines-dev/prompts/issues"
                "And ask for the model to be added to the registry."
            )
        )

    env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    env.globals["bos"] = SPECIAL_TOKENS.get(model_name, Special()).sequence.begin
    env.globals["eos"] = SPECIAL_TOKENS.get(model_name, Special()).sequence.end
    env.globals["user"] = SPECIAL_TOKENS.get(model_name, Special()).user
    env.globals["assistant"] = SPECIAL_TOKENS.get(model_name, Special()).assistant
    env.globals["system"] = SPECIAL_TOKENS.get(model_name, Special()).system
    jinja_template = env.from_string(cleaned_template)

    return jinja_template.render(**values)
