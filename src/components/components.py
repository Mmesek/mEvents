import time
from functools import wraps

import fasthtml.common as fh
from monsterui import all as mui
import mistletoe
from fasthtml import svg
from monsterui.foundations import VEnum, auto, stringify


def back_to_main():
    return fh.A(mui.Button("Wróć do listy wydarzeń", cls=mui.ButtonT.secondary, submit=False), href="/")


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


def make_icon(content: str):
    return svg.Svg(role="img", viewBox="0 0 24 24", cls="h-6 w-6 mr-1")(svg.Path(d=content), fill="currentColor")


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
                        mui.Button("Włącz powiadomienia", id="subscribe"),
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


def open_graph(title, description, thumbnail_url):
    return (
        fh.Meta(property="og:site_name", content="Mistyczne Wydarzenia Ognia i Popiołu"),
        fh.Meta(property="og:title", content=title),
        fh.Meta(property="og:description", content=description),
        fh.Meta(property="og:image", content=thumbnail_url),
        fh.Meta(property="og:type", content="article"),
        fh.Meta(name="twitter:card", content="summary"),
        fh.Meta(name="twitter:title", content=title),
        fh.Meta(name="twitter:description", content=description),
        fh.Meta(name="twitter:image", content=thumbnail_url),
    )


def Button(*args, submit: bool = True, **kwargs):
    if "type" not in kwargs:
        kwargs["type"] = "submit" if submit else "button"
    return fh.Button(*args, cls=("btn", stringify(kwargs.pop("cls", ButtonT.neutral))), **kwargs)


class ButtonT(VEnum):
    def _generate_next_value_(name, start, count, last_values):
        return f"btn-{name.replace('_', '-')}".strip("-")

    default = auto()
    """No style"""

    neutral = auto()
    """Color - neutral color"""
    primary = auto()
    """Color - primary color"""
    secondary = auto()
    """Color - secondary color"""
    accent = auto()
    """Color - accent color"""
    info = auto()
    """Color - info color"""
    success = auto()
    """Color - success color"""
    warning = auto()
    """Color - warning color"""
    error = auto()
    """Color - error color"""

    # Style
    outline = auto()
    """Style - outline style"""
    dash = auto()
    """Style - dash style"""
    soft = auto()
    """Style - soft style"""
    ghost = auto()
    """Style - ghost style"""
    link = auto()
    """Style - looks like a link"""

    # Behavior
    active = auto()
    """Behavior - looks active"""
    disabled = auto()
    """Behavior - looks disabled"""

    # Size
    xs = auto()
    """Size - Extra small size"""
    sm = auto()
    """Size - Small size"""
    md = auto()
    """Size - Medium size (default)"""
    lg = auto()
    """Size - Large size"""
    xl = auto()
    """Size - Extra large size"""

    # Modifier
    wide = auto()
    """Modifier - more horizontal padding"""
    block = auto()
    """Modifier - Full width"""
    square = auto()
    """Modifier - 1:1 ratio"""
    circle = auto()
    """Modifier - 1:1 ratio with rounded corners"""
