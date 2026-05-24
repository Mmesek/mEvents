import time, random
from fasthtml import common as fh
from src.db import supa
from supabase_auth import AuthResponse, errors


def store_session(res: AuthResponse, session: dict):
    session["email"] = res.user.email
    session["id"] = res.user.id
    session["picture"] = res.user.user_metadata.get(
        "avatar_url", f"https://api.dicebear.com/8.x/lorelei/svg?seed={res.user.id}"
    )
    session["display_name"] = res.user.user_metadata.get("name", res.user.email)
    session["auth"] = res.session.access_token
    session["refresh_token"] = res.session.refresh_token
    session["expires_at"] = res.session.expires_at


def logout(s: dict):
    s.pop("email", None)
    s.pop("id", None)
    s.pop("picture", None)
    s.pop("display_name", None)
    s.pop("auth", None)
    s.pop("refresh_token", None)
    s.pop("expires_at", None)


def user_auth_before(req, sess):
    if not sess.get("refresh_token"):
        sess["referrer"] = req.url.path
        return fh.RedirectResponse("/login", 303)


def refresh_session(req, sess):
    jitter = random.randint(60, 120)
    if sess.get("refresh_token") and (sess.get("expires_at", 0) - jitter) < time.time():
        try:
            auth = supa.auth.refresh_session(sess.get("refresh_token"))
            store_session(auth, sess)
        except errors.AuthApiError:
            supa.auth.sign_out()
            logout(sess)
            return user_auth_before(req, sess)
    elif not sess.get("refresh_token"):
        logout(sess)


def set_locale(sess):
    sess["locale"] = "pl"


STATIC = [
    r"/favicon\.ico",
    r"/static/.*",
    r".*\.css",
    r".*\.js",
    "/login",
    "/service-worker",
    "/manifest.json",
    "/icon",
]

beforeware = fh.Beforeware(
    user_auth_before,
    skip=[
        *STATIC,
        "/",
        "/events/",
        "/privacy-policy",
        "/terms-of-service",
        "/privacy-delete",
    ],
)

refreshware = fh.Beforeware(refresh_session, skip=STATIC)
