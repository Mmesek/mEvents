from functools import partial

from fasthtml import common as fh
from monsterui import all as mui


QuestionType = {
    "INPUT": partial(mui.Input),
    "ANSWER": partial(mui.Input),
    "HOUR": partial(mui.Input, type="time"),
    "DATE": partial(mui.Input, type="date"),
    "DATETIME": partial(mui.Input, type="datetime-local"),
}

QuestionTypes = {}


def register(name: str = None, type_: type = None):
    def inner(func):
        QuestionType[name or func.__name__] = func
        if type_:
            QuestionTypes[str(type_)] = func

        return func

    return inner


@register("LONG_INPUT")
def generate_long_input(**kwargs):
    return mui.TextArea(kwargs.get("default"), **kwargs)


@register("TEXT")
def generate_text(**kwargs):
    return fh.P(mui.render_md(**kwargs))


def RadioLabel(label, name, default="Yes"):
    return mui.DivLAligned(mui.Radio(name=name, checked=(label == default)), mui.FormLabel(label))


@register("CHOICE", list)
def generate_radio(question: str, options: list[str], **kwargs):
    # radio = partial(RadioLabel, name=question_id, default=kwargs.get("default"))
    return mui.LabelSelect(mui.Options(*options), label=question, **kwargs)
    # return (
    #    mui.FormLabel(question),
    #    *map(
    #        radio,
    #        options,
    #    ),
    # )


@register("BOOL", bool)
def generate_switch(**kwargs):
    return mui.Switch(value=kwargs.pop("value", None) or "on", **kwargs)


@register("SCALE")
def generate_scale(min, max, **kwargs):
    return fh.Div(
        fh.Input(
            mui.DivFullySpaced(*[fh.Span(f"{i}", cls=mui.TextPresets.muted_sm) for i in range(min, max + 1)]),
            type="range",
            min=min,
            max=max,
            value=kwargs.pop("value", None) or 0,
            **kwargs,
        )
    )
