from datetime import datetime
from functools import partial

from fasthtml import common as fh
from monsterui import all as mui

from src.components import HelpText, QuestionText

QuestionType = {}
QuestionTypes = {}


def register(name: str = None, type_: type = None):
    def inner(func):
        QuestionType[name or func.__name__] = func
        if type_:
            QuestionTypes[str(type_)] = func

        return func

    return inner


@register("INPUT", str)
@register("ANSWER", str)
def generate_input(
    question: str,
    question_id: int,
    description: str = None,
    placeholder: str = None,
    required: bool = False,
    **kwargs,
):
    return (
        QuestionText(question, required),
        HelpText(description),
        mui.Input(id=question_id, placeholder=placeholder, **kwargs),
    )


@register("LONG_INPUT")
def generate_long_input(
    question: str,
    question_id: int,
    description=None,
    placeholder=None,
    required: bool = False,
    **kwargs,
):
    return (
        QuestionText(question, required),
        HelpText(description),
        mui.TextArea(kwargs.get("default"), id=question_id, placeholder=placeholder, **kwargs),
    )


@register("TEXT")
def generate_text(description: str, *args, **kwargs):
    return fh.P(mui.render_md(description))


def RadioLabel(label, name, default="Yes"):
    return mui.DivLAligned(mui.Radio(name=name, checked=(label == default)), mui.FormLabel(label))


@register("CHOICE", list)
def generate_radio(question: str, question_id: int, options: list[str], **kwargs):
    radio = partial(RadioLabel, name=question_id, default=kwargs.get("default"))
    return (
        mui.FormLabel(question),
        *map(
            radio,
            options,
        ),
    )


@register("HOUR")
def generate_hour_picker(
    question: str,
    question_id: int,
    description: str = None,
    required: bool = False,
    **kwargs,
):
    return (
        QuestionText(question, required),
        HelpText(description),
        mui.Input(type="time", id=question_id, **kwargs),
    )


@register("BOOL", bool)
def generate_switch(question: str, question_id: int, description: str = None, **kwargs):
    return (
        mui.Switch(question, id=question_id, value=kwargs.pop("value", None) or "on", **kwargs),
        HelpText(description),
    )


@register("SCALE")
def generate_scale(
    question: str,
    question_id: int,
    min: int,
    max: int,
    description: str = None,
    required: bool = False,
    **kwargs,
):
    return (
        QuestionText(question, required),
        HelpText(description),
        mui.Range(min=min, max=max, name=question_id, **kwargs),
    )


@register("DATE")
def generate_date_picker(question: str, question_id: int, description: str, required: bool = False, **kwargs):
    return (
        QuestionText(question, required),
        HelpText(description),
        mui.Input(type="date", id=question_id, **kwargs),
    )


@register("DATETIME", datetime)
def generate_datetime_picker(question: str, question_id: int, description: str, required: bool = False, **kwargs):
    return (
        QuestionText(question, required),
        HelpText(description),
        mui.Input(type="datetime-local", id=question_id, **kwargs),
    )
