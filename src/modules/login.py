import os

import supabase
from fasthtml import common as fh
from monsterui import all as mui

from src.beforeware import store_session
from src.components.components import with_layout
from src.components.headers import HEADERS
from src.db import supa

BASE_URL = os.getenv("BASE_URL", "http://localhost:5001")
LOGIN_STRING = "Zaloguj korzystając z {}"
PROVIDERS = {
    "https://discord.com": ("discord", "Discorda"),
    "https://google.com": ("google", "Google'a"),
    # "https://facebook.com": ("facebook", "Facebook'a"),
}

app, rt = fh.fast_app(hdrs=HEADERS)


def magic_link():
    return mui.Form(
        LOGIN_STRING.format("magicznego linku"),
        mui.Input(id="email", placeholder="email@hostname.tld"),
        mui.Button("Wyślij link do logowania", cls=mui.ButtonT.primary),
        hx_post="/login/email",
    )


def provider_button(name: str, url: str):
    return fh.A(
        LOGIN_STRING.format(name[1]),
        href=url,
        hx_get="/login?provider=" + name[0],
    )


@rt("/")
@with_layout(title="Login")
def login(provider: str = None):
    if provider:
        return oauth_login(provider)
    return (
        fh.Div(
            mui.CardBody(
                "Podany (lub powiązany z metodą logowania) adres e-mail zostanie użyty do wysłania informacji organizacyjnych przed wydarzeniem (jeśli dotyczy wydarzenia)",
            ),
            *[mui.Card(provider_button(v, k)) for k, v in PROVIDERS.items()],
            mui.Card(magic_link()),
        ),
    )


def oauth_login(provider: str, scopes: list[str] = None):
    options = {"redirect_to": f"{BASE_URL}/login/redirect"}
    if scopes:
        options["scopes"] = scopes
    res = supa.auth.sign_in_with_oauth({"provider": provider, "options": options})
    return fh.Redirect(res.url)


@rt("/email")
def login_email(email: str, session):
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
        mui.Button("Użyj kodu", cls=mui.ButtonT.primary),
        hx_post="/login/otp",
    )


def finish_login(res, session):
    store_session(res, session)

    return fh.Redirect(session.get("referrer", "/"))


@rt("/otp")
def otp(otp: str, session):
    res = supa.auth.verify_otp({"email": session["otp_email"], "token": otp, "type": "email"})
    return finish_login(res, session)


@rt("/redirect")
def redirect(code: str, session):
    res = supa.auth.exchange_code_for_session({"auth_code": code})
    return finish_login(res, session)


@rt("/verify")
def verify_otp(access_token: str, type: str, session):
    res = supa.auth.verify_otp({"token_hash": access_token, "type": type})
    return finish_login(res, session)


@rt("/calendar")
def calendar():
    return oauth_login("google", ["https://www.googleapis.com/auth/calendar.events"])
