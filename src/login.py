import os

import supabase
from fasthtml.common import A, Redirect, fast_app
from monsterui.all import Card, Titled

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

app, rt = fast_app()


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


s = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)


def oauth_login(provider: str):
    res = s.auth.sign_in_with_oauth(
        {
            "provider": provider,
            "options": {"redirect_to": "http://localhost:5001/login/redirect"},
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
    res = s.auth.exchange_code_for_session({"auth_code": code})
    session["email"] = res.user.email
    return Redirect("/")
