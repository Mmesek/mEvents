from fasthtml import common as fh
from monsterui.all import Theme

from modules.login import app as login_app
from modules.events import app as events_app
from modules.forms import app as forms_app
from beforeware import beforeware

hdrs = Theme.orange.headers()


# Create your app with the theme
app, rt = fh.fast_app(
    hdrs=hdrs,
    routes=[
        fh.Mount("/login", login_app),
        fh.Mount("/events", events_app),
        fh.Mount("/forms", forms_app),
    ],
    before=beforeware,
)


@rt("/")
def index():
    return fh.Redirect("/events")


if __name__ == "__main__":
    fh.serve()
