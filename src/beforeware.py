from fasthtml import common as fh
from src.components.translations import Translation


def user_auth_before(req, sess):
    auth = req.scope["email"] = sess.get("email", None)
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
