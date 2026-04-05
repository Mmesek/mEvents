from fasthtml.common import Div, P
from monsterui.all import (
    H1,
    H3,
    Card,
    Container,
    DividerLine,
    Form,
    TextPresets,
    UkIcon,
    render_md,
    DivCentered,
)


def FormSectionDiv(*c, cls="space-y-2", **kwargs):
    return Card(*c, cls=cls, **kwargs)


def QuestionText(c, required: bool = False):
    return H3(c, cls=TextPresets.muted_sm + ("required" if required else ""))


def HelpText(c):
    return P(c, cls=TextPresets.muted_sm)


def FormLayout(title, subtitle, *content, cls="space-y-3 mt-4", destination="/submit"):
    return Container(
        DivCentered(
            H1(title),
            subtitle,
            DividerLine(),
            Form(*content, cls=cls, hx_post=destination),
        )
    )


def icon_text(icon, text, style="", icon_style=None):
    return Div(
        UkIcon(icon, cls=icon_style),
        render_md(text) if type(text) is str else text,
        cls="inline-flex space-y-0 space-x-1 justify-start items-center" + " " + style,
    )


def right_icon_text(icon, text, style="", icon_style=None):
    return Div(
        UkIcon(icon, cls=icon_style),
        render_md(text) if type(text) is str else text,
        cls="inline-flex space-y-0 space-x-1 justify-end items-center" + " " + style,
    )


def handle_updating_responses(responses: dict) -> dict:
    previous = {k.replace("previous_", ""): v for k, v in responses.items() if k.startswith("previous_") and v}
    responses = {k: v for k, v in responses.items() if not k.startswith("previous_") and v}
    diff = set(previous.keys()).difference(set(responses.keys()))
    responses.update(
        {
            k: ("off" if previous[k] == "on" else previous[k] if previous[k] in {"off", ""} else " ")
            for k in diff
            if previous.get(k)
        }
    )
    return responses
