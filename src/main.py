from fasthtml import common as fh

import src.modules.login
import src.modules.events
import src.modules.responses
import src.modules.contributions
import src.modules.tickets
import src.modules.forms
from src.components.app_factory import ROUTES

import src.modules.discord
import src.components.translations
from src.beforeware import refreshware, beforeware
from src.components.headers import HEADERS

import sentry_sdk
import dotenv
import os

dotenv.load_dotenv()
sentry_sdk.init(
    dsn=os.getenv("SENTRY_URL"),
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Enable sending logs to Sentry
    enable_logs=True,
)


# Create your app with the theme
app, rt = fh.fast_app(
    hdrs=HEADERS,
    routes=ROUTES,
    before=[refreshware, beforeware],
)



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


if __name__ == "__main__":
    fh.serve()
