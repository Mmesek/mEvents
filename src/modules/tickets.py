import base64
from datetime import datetime, timezone
from io import BytesIO

import qrcode
from fasthtml import common as fh
from monsterui import all as mui
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import CircleModuleDrawer

from src.components import TIMEZONE, with_layout
from src.components.app_factory import make_app
from src.db import Base
from src.modules.events import Event

from functools import partial

rt = make_app("tickets")


class Attendance(Base):
    event_id: int
    user_id: str
    filled_form: str | None = None
    downloaded_ticket: str | None = None
    arrived: datetime | None = None
    withdrew: str | None = None
    authorized_by: str | None = None
    created_at: datetime | None = None
    companions: int | None = None
    display_name: str | None = None


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
    Attendance.table(session["auth"]).upsert(
        {
            "event_id": event_id,
            "user_id": session["id"],
            "downloaded_ticket": datetime.now(TIMEZONE).isoformat(),
        }
    ).execute()
    return fh.Response(
        make_qr(f"https://mms-events.vercel.app/tickets/verify/{event_id}/{session['id']}"),
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=ticket-{event_id}_{session['id'][:5]}.png"},
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
    org = Event.select(session["auth"], "user_id, start_time").eq("id", event_id).maybe_single().execute().data
    if session["id"] != org["user_id"]:
        return mui.Button("Tylko organizator może zweryfikować dostęp", cls=mui.ButtonT.secondary)
    if datetime.fromisoformat(org["start_time"]).date() > datetime.now(TIMEZONE).date():
        return mui.Button(
            "Dostęp do wydarzenia można zweryfikować tylko w dniu wydarzenia!", cls=mui.ButtonT.destructive
        )
    companions = partial(
        mui.LabelInput,
        label="+1",
        id="amount",
        type="number",
        inputmode="numeric",
        min=0,
        hx_swap="replace",
        hx_target="innerHTML",
    )

    if attendance := (
        Attendance.table(session["auth"])
        .select("*")
        .eq("event_id", event_id)
        .eq("user_id", user_id)
        .not_.is_("arrived", None)
        .maybe_single()
        .execute()
    ):
        return (
            mui.Button("Dostęp został już zweryfikowany", cls=mui.ButtonT.destructive),
            mui.Form(
                companions(value=attendance.data.get("companions")),
                mui.Button(
                    "Dodaj gości",
                    hx_post=f"/tickets/verify/companions/{event_id}/{user_id}",
                    hx_target="#amount",
                    hx_swap="outerHTML",
                    cls=mui.ButtonT.ghost,
                ),
            ),
        )
    Attendance.table(session["auth"]).upsert(
        {
            "event_id": event_id,
            "user_id": user_id,
            "authorized_by": session["id"],
            "arrived": datetime.now(TIMEZONE).isoformat(),
        }
    ).execute()
    return (
        mui.Button("Zweryfikowano dostęp!", cls=mui.ButtonT.primary),
        mui.Form(
            companions(),
            mui.Button(
                "Dodaj gości",
                hx_post=f"/tickets/verify/companions/{event_id}/{user_id}",
                hx_target="#amount",
                hx_swap="outerHTML",
                cls=mui.ButtonT.ghost,
            ),
        ),
    )


@rt("/verify/companions/{event_id}/{user_id}")
def companions(session, event_id: int, user_id: str, amount: int):
    Attendance.table(session["auth"]).upsert(
        {"event_id": event_id, "user_id": user_id, "authorized_by": session["id"], "companions": amount}
    ).execute()
    return mui.Button(f"Dodano +1 w liczbie {amount}")


@rt("/verify/{event_id}/{user_id}")
def verify(session, event_id: int, user_id: str):
    return mui.DivCentered(_verify(session, event_id, user_id))


@rt("/attendance/{event_id}")
@with_layout(title="Lista uczestników")
def attendance_list(session, event_id: int):
    guests = Attendance.get(
        Attendance.select(session["auth"], "*, ...users!user_id (display_name)").eq("event_id", event_id)
    )
    return mui.DivCentered(
        fh.Ul(
            mui.Grid(
                mui.Card(mui.DivCentered(g[1].strftime("%Y/%m/%d %H:%M") if g[2] else "❌")),
                mui.Card(mui.DivCentered(g[0])),
                mui.Card(mui.DivCentered(g[2] +1)),
                cols_min=3,
            )
            for g in sorted(
                {(g.display_name, g.arrived or datetime.fromtimestamp(0, timezone.utc), g.arrived, g.amount or 0) for g in guests},
                key=lambda k: k[1],
                reverse=True,
            )
        )
    )
