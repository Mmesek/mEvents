from functools import partial

from components import HelpText, QuestionText
from fasthtml.common import P
from monsterui.all import (
    DivLAligned,
    FormLabel,
    Input,
    LabelInput,
    Radio,
    Range,
    Switch,
    TextArea,
    render_md,
)


def generate_input(
    question: str,
    question_id: int,
    description: str = None,
    placeholder: str = None,
    **kwargs,
):
    return (
        QuestionText(question),
        HelpText(description),
        Input(id=question_id, placeholder=placeholder),
    )


def generate_long_input(
    question: str, question_id: int, description=None, placeholder=None, **kwargs
):
    return (
        QuestionText(question),
        HelpText(description),
        TextArea(id=question_id, placeholder=placeholder),
    )


def generate_text(description: str, *args, **kwargs):
    return P(render_md(description))


def RadioLabel(label, name, default="Yes"):
    return DivLAligned(Radio(name=name, checked=(label == default)), FormLabel(label))


def generate_radio(question: str, question_id: int, options: list[str], **kwargs):
    radio = partial(RadioLabel, name=question_id, default=kwargs.get("default"))
    return (
        FormLabel(question),
        *map(
            radio,
            options,
        ),
    )


def generate_hour_picker(
    question: str, question_id: int, description: str = None, **kwargs
):
    return (
        QuestionText(question),
        HelpText(description),
        Input(type="time", id=question_id, **kwargs),
    )


def generate_switch(question: str, question_id: int, description: str = None, **kwargs):
    return (
        Switch(question, id=question_id, **kwargs),
        HelpText(description),
    )


def generate_scale(
    question: str,
    question_id: int,
    min: int,
    max: int,
    description: str = None,
    **kwargs,
):
    return (
        QuestionText(question),
        HelpText(description),
        Range(min=min, max=max, name=question_id, **kwargs),
    )


def generate_date_picker(question: str, question_id: int, **kwargs):
    return LabelInput(question, type="date", id=question_id, **kwargs)


QuestionType = {
    "ANSWER": generate_input,
    "INPUT": generate_input,
    "LONG_INPUT": generate_long_input,
    "CHOICE": generate_radio,
    "HOUR": generate_hour_picker,
    "DATE": generate_date_picker,
    "SCALE": generate_scale,
    "BOOL": generate_switch,
    "TEXT": generate_text,
}
