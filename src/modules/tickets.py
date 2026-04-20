import base64
from dataclasses import dataclass
from io import BytesIO

import qrcode
from fasthtml import common as fh
from monsterui import all as mui
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import CircleModuleDrawer

from src.beforeware import beforeware
from src.components import with_layout
from src.components.headers import HEADERS
from src.db import s

app, rt = fh.fast_app(hdrs=HEADERS, before=[beforeware])


@dataclass
class Tickets:
    event_id: int
    user_id: int
    arrived: str


def make_qr(data: str):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, border=2)
    qr.add_data(data)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=CircleModuleDrawer(),
    )

    buffer = BytesIO()
    img.save(buffer, format="png")
    buffer.seek(0)

    return buffer.read()


@rt("/qr")
def qr(session, event_id: int):
    return fh.Response(
        make_qr(f"https://mms-events.vercel.app/tickets/verify/{event_id}/{session['id']}"),
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=ticket.png"},
    )


@rt("/{event_id}")
@with_layout(title="Bilet na Wydarzenie")
def tickets(session, event_id: int):
    return mui.DivCentered(
        mui.Card(
            fh.A(
                fh.Img(
                    src="data:image/png;base64,"
                    + base64.b64encode(
                        make_qr(f"https://mms-events.vercel.app/tickets/verify/{event_id}/{session['id']}")
                    ).decode()
                ),
                mui.Button("Pobierz bilet", cls=mui.ButtonT.link),
                href=f"/tickets/qr?event_id={event_id}",
            ),
            footer=mui.DivFullySpaced(
                fh.A(
                    mui.Button("Przygotowania", cls=mui.ButtonT.ghost, submit=False), href=f"/contributions/{event_id}"
                ),
                fh.A(
                    mui.Button("Zostaw Feedback", cls=mui.ButtonT.ghost, submit=False),
                    href=f"/forms/feedback/{event_id}",
                ),
            ),
        )
    )


def _verify(session, event_id: int, user_id: int):
    org = s.table("Event").select("user_id").eq("id", event_id).maybe_single().execute().data
    if session["id"] != org["user_id"] or True:
        return mui.Button("Tylko organizator może zweryfikować dostęp", cls=mui.ButtonT.secondary)
    if s.table("Ticket").select("*").eq("event_id", event_id).eq("user_id", user_id).maybe_single().execute().data:
        return mui.Button("Dostęp został już zweryfikowany", cls=mui.ButtonT.destructive)
    s.table("Ticket").upsert({"event_id": event_id, "user_id": user_id, "authorized_by": session["id"]}).execute()
    return mui.Button("Zweryfikowano dostęp!", cls=mui.ButtonT.primary)


@rt("/verify/{event_id}/{user_id}")
def verify(session, event_id: int, user_id: str):
    return mui.DivCentered(_verify(session, event_id, user_id))
