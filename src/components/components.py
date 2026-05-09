import time
from functools import wraps

import fasthtml.common as fh
from monsterui import all as mui
import mistletoe


def FormSectionDiv(*c, cls="space-y-2", **kwargs):
    return mui.Card(*c, cls=cls, **kwargs)


def QuestionText(c, required: bool = False):
    return mui.H3(c, cls=mui.TextPresets.muted_sm + ("required" if required else ""))


def HelpText(c):
    if c:
        return fh.NotStr(mistletoe.markdown(c.strip()))  # , cls=mui.TextPresets.muted_sm)


def FormLayout(title, subtitle, *content, cls="space-y-3 mt-4", destination="/submit"):
    return mui.Container(
        mui.DivCentered(
            mui.H1(title),
            subtitle,
            mui.DividerLine(),
            mui.Form(*content, cls=cls, hx_post=destination),
        )
    )


def icon_text(icon, text, style="", icon_style=None):
    return fh.Div(
        mui.UkIcon(icon, cls=icon_style),
        mui.render_md(text) if type(text) is str else text,
        cls="inline-flex space-y-0 space-x-1 justify-start items-center" + " " + style,
    )


def right_icon_text(icon, text, style="", icon_style=None):
    return fh.Div(
        mui.UkIcon(icon, cls=icon_style),
        mui.render_md(text) if type(text) is str else text,
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
                mui.DivRAligned(
                    "Zalogowano jako:",
                    fh.Img(src=session.get("picture"), height="24", width="24"),
                    session.get("email"),
                )
                if session.get("email")
                else None,
            ),
            mui.DivCentered(mui.H1(title)),
            mui.DivCentered(*body),
            fh.Footer(
                mui.Card(
                    footer=mui.DivCentered(
                        mui.DivLAligned(
                            *[mui.UkIconLink(icon, href=url) for icon, url in socials],
                            mui.DivRAligned(f"Page generated in {t:>.3}s"),
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
