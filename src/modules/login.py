import os

from fasthtml.common import A, Redirect, fast_app, P
from monsterui.all import (
    Card,
    Titled,
    Theme,
    Form,
    Input,
    Button,
    ButtonT,
)

from src.db import supa

BASE_URL = os.getenv("BASE_URL", "http://localhost:5001")

app, rt = fast_app(hdrs=Theme.orange.headers())

LOGIN_STRING = "Zaloguj korzystając z {}"


def magic_link():
    return Form(
        LOGIN_STRING.format("magicznego linku"),
        Input(id="email", placeholder="email@hostname.tld"),
        Button("Wyślij link do logowania", cls=ButtonT.primary),
        hx_post="/login/email",
    )


@rt("/")
def login():
    return Titled(
        "Login",
        Card(
            A(
                LOGIN_STRING.format("Discorda"),
                href="https://discord.com",
                hx_get="/login/discord",
            ),
        ),
        Card(
            A(
                LOGIN_STRING.format("Google'a"),
                href="https://google.com",
                hx_get="/login/google",
            )
        ),
        Card(magic_link()),
    )


def oauth_login(provider: str):
    res = supa.auth.sign_in_with_oauth(
        {
            "provider": provider,
            "options": {"redirect_to": f"{BASE_URL}/login/redirect"},
        }
    )
    return Redirect(res.url)


@rt("/discord")
def login_discord():
    return oauth_login("discord")


@rt("/facebook")
def login_facebook():
    return oauth_login("facebook")


@rt("/google")
def login_google():
    return oauth_login("google")


@rt("/email")
def login_email(email: str, session):
    try:
        res = supa.auth.sign_in_with_otp(
            {
                "email": email,
                "options": {"email_redirect_to": f"{BASE_URL}/login/verify"},
            }
        )
    except:
        return "Wprowadzony adres e-mail jest nie poprawny", magic_link()
    session["otp_email"] = email
    return P(
        "Sprawdź swojego maila oraz kliknij w link bądź wpisz tutaj kod z maila aby się zalogować:"
    ), Form(
        Input(id="otp", placeholder="123456"),
        Button("Użyj kodu", cls=ButtonT.primary),
        hx_post="/login/otp",
    )


@rt("/otp")
def otp(otp: str, session):
    res = supa.auth.verify_otp(
        {"email": session["otp_email"], "token": otp, "type": "email"}
    )
    session["email"] = res.user.email
    session["id"] = res.user.id
    session["picture"] = f"https://api.dicebear.com/8.x/lorelei/svg?seed={res.user.id}"
    return Redirect(session.get("referrer", "/"))


@rt("/redirect")
def redirect(code: str, session):
    res = supa.auth.exchange_code_for_session({"auth_code": code})
    session["email"] = res.user.email
    session["id"] = res.user.id
    session["picture"] = res.user.user_metadata.get("avatar_url")

    return Redirect(session.get("referrer", "/"))


@rt("/verify")
def verify_otp(access_token: str, type: str, session):
    res = supa.auth.verify_otp({"token_hash": access_token, "type": type})
    session["email"] = res.user.email
    session["id"] = res.user.id
    session["picture"] = f"https://api.dicebear.com/8.x/lorelei/svg?seed={res.user.id}"

    return Redirect(session.get("referrer", "/"))
