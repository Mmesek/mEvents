import os

import supabase
from fasthtml import common as fh
from monsterui import all as mui

from src.beforeware import store_session
from src.components.app_factory import add_mount
from src.components.components import with_layout
from src.components.headers import HEADERS
from src.db import supa
from src import components as mu

BASE_URL = os.getenv("BASE_URL", "http://localhost:5001")

PROVIDER_LIST = [
    "Discord",
    "Google",
    # "Facebook",
    # "GitHub",
    # "Solana",
    # "Etherum",
    # "Twitch",
    # "Spotify",
    # "X/Twitter",
    # "LinkedIn",
    # "GitLab",
    # "Apple",
]
PROVIDERS = {}
for p in PROVIDER_LIST:
    with open(f"static/icons/{p.lower()}.svg", encoding="utf-8") as file:
        PROVIDERS[p] = fh.NotStr(file.read())

app, rt = mui.fast_app(hdrs=HEADERS)
add_mount("login", app)


def magic_link():
    return mui.Form(
        mui.Input(id="email", placeholder="email@hostname.tld", required=True),
        mu.Button("Wyślij link do logowania", cls=(mu.ButtonT.primary, "w-full")),
        hx_post="/login/email",
    )


def provider_button(name: str, url: str):
    return mu.Button(url, name, hx_get="/login?provider=" + name.lower(), cls=mu.ButtonT.secondary)


@with_layout(title="Login")
def index():
    return (
        mui.Card(
            mui.Small(
                "Podany (lub powiązany z metodą logowania) adres e-mail zostanie użyty do wysłania informacji organizacyjnych przed wydarzeniem (jeśli dotyczy wydarzenia)",
            ),
            mui.DividerSplit(mui.Small("Kontynuuj z")),
            mui.Grid(*[provider_button(k, v) for k, v in PROVIDERS.items()], cols=min(3, len(PROVIDERS))),
            mui.DividerSplit(mui.Small("Albo użyj magicznego linku"), cls=mui.TextT.muted),
            mui.Card(magic_link()),
            # mui.DivVStacked(
            #    mui.Small(
            #        "Kontynuując, zgadasz się na ",
            #        fh.A(cls=mui.AT.muted, href="#my-modal")("Warunki Korzystania"),
            #        " oraz ",
            #        fh.A(cls=mui.AT.muted, href="#privacy-policy")("Politykę Prywatności"),
            #        ".",
            #        cls=(mui.TextT.muted, "text-center"),
            #    )
            # ),
        ),
    )


@rt("/")
def login(provider: str = None):
    if provider:
        return oauth_login(provider)
    return index()


def oauth_login(provider: str, scopes: list[str] = None):
    options = {"redirect_to": f"{BASE_URL}/login/redirect"}
    if scopes:
        options["scopes"] = scopes
    res = supa.auth.sign_in_with_oauth({"provider": provider, "options": options})
    return fh.Redirect(res.url)


@rt("/email")
def login_email(email: str, session):
    if not email:
        return magic_link()
    try:
        supa.auth.sign_in_with_otp(
            {
                "email": email,
                "options": {"email_redirect_to": f"{BASE_URL}/login/verify"},
            }
        )
    except supabase.AuthApiError:
        return "Wprowadzony adres e-mail jest nie poprawny", magic_link()
    session["otp_email"] = email
    return fh.P("Sprawdź swojego maila oraz kliknij w link bądź wpisz tutaj kod z maila aby się zalogować:"), mui.Form(
        mui.Input(id="otp", placeholder="123456"),
        mu.Button("Użyj kodu", cls=mu.ButtonT.primary),
        hx_post="/login/otp",
    )


def finish_login(res, session):
    store_session(res, session)

    return fh.Redirect(session.pop("referrer", "/"))


@rt("/otp")
def otp(otp: str, session):
    try:
        res = supa.auth.verify_otp({"email": session["otp_email"], "token": otp, "type": "email"})
    except supabase.AuthApiError as ex:
        return fh.P("Błąd: ", ex)
    return finish_login(res, session)


@rt("/redirect")
def redirect(code: str, session):
    try:
        res = supa.auth.exchange_code_for_session({"auth_code": code})
    except supabase.AuthApiError as ex:
        return fh.P("Błąd: ", ex)
    return finish_login(res, session)


@rt("/verify")
def verify_otp(access_token: str, type: str, session):
    try:
        res = supa.auth.verify_otp({"token_hash": access_token, "type": type})
    except supabase.AuthApiError as ex:
        return fh.P("Błąd: ", ex)
    return finish_login(res, session)


@rt("/calendar")
def calendar():
    return oauth_login("google", ["https://www.googleapis.com/auth/calendar.events"])


@rt("/link-identity")
def link_identity(provider: str):
    res = supa.auth.link_identity({"provider": provider})
    return fh.Redirect(res.url)
