import os
from fasthtml import common as fh
from msgspec import json

from src.db import Base
from src.root import rt
from src.components.headers import HEADERS

with open("static/service-worker.js", encoding="utf-8") as file:
    SERVICE_WORKER = file.read()

with open("static/app.js", encoding="utf-8") as file:
    HEADERS.append(
        fh.Script(
            file.read()
            .replace("{VAPID_PUBLIC_KEY}", os.getenv("VAPID_PUBLIC_KEY"))
            .replace("{BASE_URL}", os.getenv("BASE_URL", "http://localhost:5001"))
        )
    )

with open("static/manifest.json", encoding="utf-8") as file:
    MANIFEST = json.decode(file.read())

MANIFEST["name"] = os.getenv("APP_NAME", "Name")
MANIFEST["short_name"] = os.getenv("SHORT_NAME", "Short Name")
MANIFEST["icons"][0]["src"] = os.getenv("ICON_192", "/icon.png")
MANIFEST["icons"][1]["src"] = os.getenv("ICON_512", "/icon.png")


class Notification(Base):
    user_id: str
    subscription: str
    scope: str = "events"


@rt("/service-worker")
def service_worker():
    return fh.Response(
        SERVICE_WORKER,
        media_type="text/javascript",
    )


@rt("/manifest.json")
def manifest():
    return fh.Response(str(MANIFEST), media_type="application/json")


@rt("/notification/register")
def save_token(session, subscription: str):
    Notification(None, subscription=subscription).upsert(session["auth"])
    return {"status": True}
