from fasthtml import common as fh


def user_auth_before(req, sess):
    auth = req.scope["email"] = sess.get("email", None)
    if not auth:
        sess["referrer"] = req.url.path
        return fh.RedirectResponse("/login", 303)


beforeware = fh.Beforeware(
    user_auth_before,
    skip=[
        r"/favicon\.ico",
        r"/static/.*",
        r".*\.css",
        r".*\.js",
        "/login",
        "/",
        "/events",
        "/privacy-policy",
        "/terms-of-service",
        "/privacy-delete",
    ],
)
