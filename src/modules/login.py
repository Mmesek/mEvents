import os

from fasthtml.common import A, Redirect, fast_app
from monsterui.all import Card, Titled, Theme

from db import supa

BASE_URL = os.getenv("BASE_URL", "http://localhost:5001")

app, rt = fast_app(hdrs=Theme.orange.headers())


@rt("/")
def login():
    return Titled(
        "Login",
        Card(
            A(
                "Login with Discord",
                href="https://discord.com",
                hx_get="/login/discord",
            ),
        ),
        Card(
            A(
                "Login with Facebook",
                href="https://facebook.com",
                hx_get="/login/facebook",
            ),
        ),
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


@rt("/redirect")
def redirect(code: str, session):
    res = supa.auth.exchange_code_for_session({"auth_code": code})
    session["email"] = res.user.email
    session["id"] = res.user.id
    session["picture"] = res.user.user_metadata.get("avatar_url")

    return Redirect("/")
