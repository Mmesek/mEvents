import time
from collections.abc import Iterable
from functools import wraps

import fasthtml.common as fh
from fasthtml.common import Div, P
from monsterui.all import (
    H1,
    H3,
    Card,
    Container,
    DivCentered,
    DividerLine,
    DivLAligned,
    DivRAligned,
    Form,
    TextPresets,
    UkIcon,
    UkIconLink,
    render_md,
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


def Layout(body, title: str = None, *, session: dict = None, t: float):
    socials = (
        ("github", "https://github.com/Mmesek/mEvents"),
        # ("messages-square", "https://discord.com"),
    )

    return (
        fh.Title(title),
        fh.Main(
            fh.Header(
                DivRAligned(
                    "Zalogowano jako:",
                    fh.Img(src=session.get("picture"), height="24", width="24"),
                    session.get("email"),
                )
                if session.get("email")
                else None,
            ),
            DivCentered(H1(title)),
            DivCentered(*body),
            fh.Footer(
                Card(
                    footer=DivCentered(
                        DivLAligned(
                            *[UkIconLink(icon, href=url) for icon, url in socials],
                            DivRAligned(f"Page generated in {t:>.3}s"),
                        ),
                    ),
                ),
            ),
        ),
    )


def with_layout(layout=Layout, *args, **kwargs):
    def inner(f):
        @wraps(f)
        def wrapper(*inner_args, **inner_kwargs):
            s = time.time()
            r = f(*inner_args, **inner_kwargs)
            return layout(r, *args, session=inner_kwargs.get("session", {}), t=time.time() - s, **kwargs)

        return wrapper

    return inner
