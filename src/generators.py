from functools import partial

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


def info_card(
    title=None,
    start=None,
    end=None,
    date=None,
    place=None,
    theme=None,
    dresscode=None,
    dresscode_mandatory=None,
    discord_event=None,
    description=None,
    image=None,
    count=None,
    href=None,
    organizer=None,
):
    if dresscode and not dresscode_mandatory:
        dresscode += " *(Opcjonalnie)*"
    align = right_icon_text if count else icon_text
    return DivCentered(
        Card(
            Img(
                src=image,
                loading="lazy",
                width=1000,
                height=400,
                style="max-height: 400px;",
            )
            if image
            else None,
            DivCentered(H1(title)),
            Grid(
                icon_text("clock", f"{start}"),
                right_icon_text("clock-10", f"{end}"),
                cols=2,
                cls="gap-1 items-center justify-center",
            ),
            Grid(
                icon_text("calendar", f"{date}"),
                right_icon_text("pin", f"{place}"),
                (icon_text("users", f"**Liczba zapisanych**: {count}"))
                if count
                else None,
                (align("user", f"**Organizator**: {organizer}")) if organizer else None,
                cols=2,
                cls="gap-1",
            ),
            (icon_text("palette", f"**Temat Przewodni**: {theme}")) if theme else None,
            (icon_text("shirt", f"**Dresscode**: {dresscode}")) if dresscode else None,
            DivCentered(
                icon_text(
                    "messages-square",
                    text=f"**[Discord]({discord_event})**",
                )
            )
            if discord_event
            else None,
            DivCentered(render_md(description)) if description else None,
            DivRAligned(
                A(
                    Button("Weź udział", cls=ButtonT.ghost, submit=False),
                    href=href,
                )
            ),
            body_cls="space-y-0",
        )
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
        Input(id=question_id, placeholder=placeholder, **kwargs),
    )


def generate_long_input(
    question: str, question_id: int, description=None, placeholder=None, **kwargs
):
    return (
        QuestionText(question),
        HelpText(description),
        TextArea(
            kwargs.get("default"), id=question_id, placeholder=placeholder, **kwargs
        ),
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
