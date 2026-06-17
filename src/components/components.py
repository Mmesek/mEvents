import time
from functools import wraps

import fasthtml.common as fh
from monsterui import all as mui
import mistletoe
from fasthtml import svg
from monsterui.foundations import VEnum, auto, stringify

import os
import dotenv
from msgspec import json

dotenv.load_dotenv()
SOCIALS = (
    ("github", "https://github.com/Mmesek/mEvents"),
    *json.decode(os.getenv("SOCIALS", "{}")).items(),
)

HEADER = [
    ("/events", "Główna", "home", ""),
    # ("/tickets/mine", "Bilety", "tickets", ""),
    # ("/events/reviews", "Recenzje", "square-pen", ""),
    # ("/events/mine", "Moje Wydarzenia", "calendar", ""),
    # ("/events/create", "Utwórz", "calendar-plus", ""),
]

FOOTER = [
    [
        ("", "Strona", ""),
        ("/", "Główna", "home"),
        ("/profile", "Profil", "user"),
        #    ("/events", "Wydarzenia", "calendar"),
        #    ("/tickets", "Bilety", "tickets"),
        #    ("/feedback", "Recenzje", "square-pen"),
    ],
    # [
    #    ("", "Info", ""),
    #    ("/about/", "O Nas", "info"),
    #    ("/contact/", "Kontakt", "contact"),
    #    ("https://mmesek.github.io/pl", "Blog", "rss")
    #    ("", "Legal", ""),
    #    ("/privacy-policy", "Polityka Prywatności", "cookie"),
    #    ("/terms-of-service", "Regulamin", "book-text"),
    # ],
]
MENU_LINKS = [("/events/create", "calendar-plus", "Utwórz wydarzenie")]


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


LINK_HOVER = "link link-hover"
ICON_LINK = "space-x-1 inline-flex items-center"


def LinkIconHover(url: str, title: str = None, icon: str = None):
    return fh.Div(
        mui.UkIcon(icon) if icon else None,
        fh.A(
            title if title else None,
            href=url,
            cls=LINK_HOVER,
            title=title,
        ),
        cls=ICON_LINK,
    )


def LinkSvgHover(url: str, title: str = None, icon: str = None):
    return fh.Div(
        fh.Img(src=f"/static/icons/{icon.lower()}.svg", style="filter: invert(1);", width=16, height=16),
        fh.A(
            title if title else None,
            href=url,
            cls=LINK_HOVER,
            title=title,
        ),
        cls=ICON_LINK,
    )


def URLButton(url: str, *args, title: str = None, **kwargs):
    return fh.A(mui.Button(*args, **kwargs), href=url, title=title)


def header_navbar(session, title: str):
    return fh.Header(
        fh.Nav(
            fh.Div(
                fh.Div(
                    Link("/", "Mistyczne Wydarzenia Ognia i Popiołu", ""),
                    cls="hidden sm:flex items-center",
                ),
                fh.Div(mui.H1(title), cls="hidden md:flex items-center"),
                fh.Div(
                    fh.Div(
                        *[Link(url, tooltip, icon, title) for url, tooltip, icon, title in HEADER],
                        cls="hidden sm:flex",
                    ),
                    (
                        Link(
                            "/profile/",
                            "Profil",
                            "user",
                            (
                                fh.Img(src=session.get("picture"), height="24", width="24"),
                                session.get("email"),
                            ),
                        ),
                        Link("/login/", "Wyloguj", "log-out", ""),
                    )
                    if session.get("email")
                    else Link("/login/", "Zaloguj", "log-in", ""),
                    burger_menu(MENU_LINKS)
                    if session.get("email") and session.get("id", "").startswith("469a8cdb")
                    else None,
                    cls="flex items-center space-x-4",
                ),
                cls="flex justify-between items-center w-full space-x-4",
            ),
            cls="navbar bg-black glass",
        ),
    )


def generate_links(links: list[tuple[str, str, str]]):
    return [LinkIconHover(url, title, icon) if url else fh.H6(title, cls="footer-title") for url, title, icon in links]


def footer_navbar(t):
    return fh.Footer(
        fh.Aside(
            fh.H6("Mistyczne Wydarzenia", cls="footer-title"),
            icon_text("timer", fh.P(f"{t:>.2}s")),
            fh.P("Made w/o ☕ by ", fh.A("Mmesek", href="https://github.com/Mmesek", cls=ButtonT.link)),
            fh.P("Copyright @ 2026"),
        ),
        fh.Nav(
            fh.H6("Społeczność", cls="footer-title"),
            *[LinkSvgHover(url, icon.title(), icon) for icon, url in SOCIALS],
        )
        if SOCIALS
        else None,
        *[fh.Nav(*generate_links(column)) for column in FOOTER],
        fh.Div(
            fh.H6("Push o nowych wydarzeniach", cls="footer-title"),
            Button(icon_text("bell", "Włącz powiadomienia"), id="subscribe", cls=ButtonT.accent),
        ),
        cls="footer sm:footer-horizontal xs:footer-center glass bg-black text-base-content p-4 text-center justify-center sm:w-full",
    )


def Layout(body, title: str = None, *, session: dict = None, t: float):
    return (
        fh.Title(title),
        fh.Main(
            header_navbar(session, title),
            mui.DivCentered(mui.H1(title), cls="md:hidden"),
            mui.DivCentered(*body),
            # fab(),
            footer_navbar(t),
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


def CopyToClipboard(
    url: str, message: str = "Skopiowano link do wydarzenia!", title: str = "Skopiuj link do wydarzenia"
):
    return Button(
        icon_text("copy", ""),
        cls=ButtonT.link,
        onclick=f"""
    navigator.clipboard.writeText('{url}'); const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = '<div class="alert alert-success" style="max-width: fit-content"><span>{message}</span></div>'
    toast.style.left = (event.clientX + 10) + 'px';
    toast.style.top = (event.clientY + 10) + 'px';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 1000);""",
        title=title,
    )


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


def Link(
    url: str, title: str = None, icon: str = None, icon_title: str = None, cls: ButtonT | str = ButtonT.ghost, **kwargs
):
    return fh.A(
        mui.UkIcon(icon) if icon else None,
        title if icon_title is None else icon_title,
        href=url,
        cls=cls + "btn inline-flex items-center",
        title=title,
        **kwargs,
    )


def LinkButton(url: str, title: str = None, cls: ButtonT | str = ButtonT.ghost, tooltip: str = None, **kwargs):
    return fh.A(Button(title, cls=(cls, "inline-flex items-center"), submit=False, title=tooltip, **kwargs), href=url)


def ReplaceButton(title: str, url: str, target: str, cls: ButtonT | str = ButtonT.secondary):
    return fh.Div(
        Button(
            title,
            hx_target=f"#{target}",
            hx_get=url,
            cls=cls,
        ),
        id=f"{target}",
    )


from functools import partial

LinkSecondary = partial(LinkButton, cls=ButtonT.secondary)
LinkPrimary = partial(LinkButton, cls=ButtonT.primary)
LinkDanger = partial(LinkButton, cls=ButtonT.error)
LinkNeutral = partial(Link, cls=ButtonT.neutral)


def burger_menu(links: list[tuple[str, str, str]]):
    return fh.Nav(
        fh.Div(
            Button(mui.UkIcon("plus"), tabindex=0, role="button", cls=("btn", ButtonT.ghost)),
            fh.Ul(
                fh.Li(fh.A(mui.UkIcon(icon), title, href=url) for url, icon, title in links),
                tabindex="0",
                cls="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52",
            ),
            cls="dropdown dropdown-end",
        ),
        cls="navbar",
    )


def fab(links: list[tuple[str, str, str]]):
    return fh.Div(
        fh.Div(
            mui.UkIcon("plus"), tabindex=0, role="button", cls=("btn", ButtonT.circle, ButtonT.secondary, ButtonT.lg)
        ),
        *[
            LinkSecondary(url, mui.UkIcon(icon), cls=ButtonT.circle + ButtonT.lg + ButtonT.secondary, tooltip=tooltip)
            for url, icon, tooltip in links
        ],
        cls="fab",
    )


def Select(title: str, *options: list[fh.Option], id: str, placeholder: str = None, **kwargs):
    return fh.Fieldset(
        fh.Legend(title, cls="fieldset-legend"),
        fh.Select(
            fh.Option(placeholder, disabled=True, selected=True, value=None) if placeholder else None,
            *options,
            id=id,
            **kwargs,
            cls="select",
        ),
        cls="fieldset",
    )
