from fasthtml import common as fh
from monsterui.all import Theme

from src.modules.login import app as login_app
from src.modules.events import app as events_app
from src.modules.forms import app as forms_app
from src.beforeware import beforeware

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
def index(code: str = None):
    if code:
        return fh.Redirect(f"/login/redirect?code={code}")
    return fh.Redirect("/events")


@rt("/privacy-policy")
def privacy():
    return fh.P(
        "Twój adres e-mail jest przetwarzany w celach wysłania e-maila z zaproszeniem do kalendarza."
    )


@rt("/terms-of-service")
def tos():
    return fh.P("Poważnie?")


@rt("/privacy-delete")
def deleteme():
    return fh.P("Skontaktuj się z @Mmesek w celu usunięcia twoich danych.")


if __name__ == "__main__":
    fh.serve()
