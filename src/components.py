from fasthtml.common import Div, P
from monsterui.all import (
    H1,
    H3,
    Card,
    Container,
    DividerLine,
    DivLAligned,
    Form,
    TextPresets,
    UkIcon,
    render_md,
)


def FormSectionDiv(*c, cls="space-y-2", **kwargs):
    return Card(*c, cls=cls, **kwargs)


def QuestionText(c):
    return H3(c, cls=TextPresets.muted_sm)


def HelpText(c):
    return P(c, cls=TextPresets.muted_sm)


def FormLayout(title, subtitle, *content, cls="space-y-3 mt-4"):
    return Container(Div(H1(title), subtitle, DividerLine(), Form(*content, cls=cls)))


def icon_text(icon, text):
    return (
        DivLAligned(
            UkIcon(icon),
            render_md(text),
            cls="space-y-0 space-x-1",
        ),
    )


def right_icon_text(icon, text):
    return (
        DivLAligned(
            render_md(text),
            UkIcon(icon),
            cls="space-y-0 space-x-1",
        ),
    )
