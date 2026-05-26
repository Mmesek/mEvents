from fasthtml import common as fh
from src.components.app_factory import ROUTES
from src.components.headers import HEADERS

# Create your app with the theme
app, rt = fh.fast_app(hdrs=HEADERS, routes=ROUTES)


@rt("/")
def index(code: str = None):
    if code:
        return fh.Redirect(f"/login/redirect?code={code}")
    return fh.Redirect("/events")


@rt("/privacy-policy")
def privacy():
    return fh.P("Twój adres e-mail jest przetwarzany w celach wysłania e-maila z zaproszeniem do kalendarza.")


@rt("/terms-of-service")
def tos():
    return fh.P("Poważnie?")


@rt("/privacy-delete")
def deleteme():
    return fh.P("Skontaktuj się z @Mmesek w celu usunięcia twoich danych.")
