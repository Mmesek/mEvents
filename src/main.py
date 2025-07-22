from fasthtml import common as fh
from monsterui.all import Theme

from modules.login import app as login_app
from modules.events import app as events_app
from modules.forms import app as forms_app

hdrs = Theme.orange.headers()


def user_auth_before(req, sess):
    auth = req.scope["email"] = sess.get("email", None)
    if not auth:
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
    ],
)

# Create your app with the theme
app, rt = fh.fast_app(
    hdrs=hdrs,
    routes=[
        fh.Mount("/login", login_app),
        fh.Mount("/events", events_app),
        fh.Mount("/form", forms_app),
    ],
    before=beforeware,
)


@rt("/")
def index():
    return fh.Redirect("/events")


if __name__ == "__main__":
    fh.serve()
