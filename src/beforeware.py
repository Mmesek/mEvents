import time
from fasthtml import common as fh
from src.components.translations import Translation
from src.db import supa
from supabase_auth import AuthResponse


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


def user_auth_before(req, sess):
    auth = req.scope["email"] = sess.get("email", None)
    if sess.get("expires_at", 0) < time.time():
        auth = supa.auth.refresh_session(sess.get("refresh_token"))
        store_session(auth, sess)
    if not auth:
        sess["referrer"] = req.url.path
        return fh.RedirectResponse("/login", 303)


def set_locale(sess):
    sess["locale"] = "pl"
    # sess.t = Translation(sess.get("locale"))


beforeware = fh.Beforeware(
    user_auth_before,
    skip=[
        r"/favicon\.ico",
        r"/static/.*",
        r".*\.css",
        r".*\.js",
        "/login",
        "/",
        "/events/",
        "/privacy-policy",
        "/terms-of-service",
        "/privacy-delete",
    ],
)

translations = fh.Beforeware(set_locale)
