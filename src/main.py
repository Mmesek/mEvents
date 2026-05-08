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
if os.getenv("SENTRY_URL"):
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


from src.modules.pwa import MANIFEST, SERVICE_WORKER, SVG, Notification


@rt("/manifest.json")
def manifest():
    return fh.Response(MANIFEST, media_type="application/json")


@rt("/service-worker")
def service_worker():
    return fh.Response(
        SERVICE_WORKER,
        media_type="text/javascript",
    )


@rt("/icon")
def icon():
    return fh.Response(SVG, media_type="image/svg+xml")


@rt("/notification/register")
def save_token(session, subscription: str):
    Notification.table(session["auth"]).upsert({"subscription": subscription}).execute()
    return {"status": True}


if __name__ == "__main__":
    fh.serve()
