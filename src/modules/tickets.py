import base64
from io import BytesIO

import qrcode
from fasthtml import common as fh
from monsterui import all as mui
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import CircleModuleDrawer

from src.components import with_layout
from src.components.app_factory import make_app
from src.db import Base
from src.modules.events import Event

rt = make_app("tickets")


class Attendance(Base):
    event_id: int
    user_id: int
    filled_form: str
    downloaded_ticket: str
    arrived: str
    withdrew: str
    authorized_by: str


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
    org = Event.select(session["auth"], "user_id").eq("id", event_id).maybe_single().execute().data
    if session["id"] != org["user_id"]:
        return mui.Button("Tylko organizator może zweryfikować dostęp", cls=mui.ButtonT.secondary)
    if (
        Attendance.table(session["auth"])
        .select("*")
        .eq("event_id", event_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    ):
        return mui.Button("Dostęp został już zweryfikowany", cls=mui.ButtonT.destructive)
    Attendance.table(session["auth"]).upsert(
        {"event_id": event_id, "user_id": user_id, "authorized_by": session["id"]}
    ).execute()
    return mui.Button("Zweryfikowano dostęp!", cls=mui.ButtonT.primary)


@rt("/verify/{event_id}/{user_id}")
def verify(session, event_id: int, user_id: str):
    return mui.DivCentered(_verify(session, event_id, user_id))
