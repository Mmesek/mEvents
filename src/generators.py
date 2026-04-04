from functools import partial
from datetime import datetime

from fasthtml.common import P, Img, A
from monsterui.all import (
    DivLAligned,
    DivRAligned,
    FormLabel,
    Input,
    LabelInput,
    Radio,
    Range,
    Switch,
    TextArea,
    render_md,
    H1,
    Card,
    DivCentered,
    Grid,
    Button,
    ButtonT,
)

from src.components import HelpText, QuestionText, icon_text, right_icon_text

QuestionType = {}
QuestionTypes = {}


def register(name: str = None, type_: type = None):
    def inner(func):
        QuestionType[name or func.__name__] = func
        if type_:
            QuestionTypes[str(type_)] = func

        return func

    return inner


def guests(event_id: str, target: str = "guestlist"):
    return Button(
        "Lista gości",
        cls=ButtonT.ghost,
        submit=False,
        hx_target=f"#{target}",
        hx_get=f"/forms/guests?event_id={event_id}",
    )


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
        Input(id=question_id, placeholder=placeholder, **kwargs),
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
        TextArea(
            kwargs.get("default"), id=question_id, placeholder=placeholder, **kwargs
        ),
    )


@register("TEXT")
def generate_text(description: str, *args, **kwargs):
    return P(render_md(description))


def RadioLabel(label, name, default="Yes"):
    return DivLAligned(Radio(name=name, checked=(label == default)), FormLabel(label))


@register("CHOICE", list)
def generate_radio(question: str, question_id: int, options: list[str], **kwargs):
    radio = partial(RadioLabel, name=question_id, default=kwargs.get("default"))
    return (
        FormLabel(question),
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
        Input(type="time", id=question_id, **kwargs),
    )


@register("BOOL", bool)
def generate_switch(question: str, question_id: int, description: str = None, **kwargs):
    return (
        Switch(question, id=question_id, **kwargs),
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
        Range(min=min, max=max, name=question_id, **kwargs),
    )


@register("DATE")
def generate_date_picker(question: str, question_id: int, **kwargs):
    return LabelInput(question, type="date", id=question_id, **kwargs)


@register("DATETIME", datetime)
def generate_datetime_picker(question: str, question_id: int, **kwargs):
    return LabelInput(question, type="datetime-local", id=question_id, **kwargs)
