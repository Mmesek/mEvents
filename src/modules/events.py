from dataclasses import dataclass
from datetime import datetime

from fasthtml import common as fh
from monsterui.all import (
    AT,
    H1,
    Card,
    DivCentered,
    DivLAligned,
    UkIconLink,
)

from src.db import s
from src.generators import info_card
from src.modules.headers import HEADERS


@dataclass
class Event:
    id: int
    title: str
    description: str
    form_id: int
    feedback_form_id: int
    user_id: str
    place: str
    start_time: datetime
    end_time: datetime | None
    theme: str | None
    dresscode: str | None
    dresscode_mandatory: bool
    discord_event: str | None
    wrap: str
    image: str
    responses: list[dict]
    org_name: str

    def __post_init__(self):
        self.start_time = datetime.fromisoformat(self.start_time)
        if self.end_time:
            self.end_time = datetime.fromisoformat(self.end_time)


app, rt = fh.fast_app(hdrs=HEADERS)


@rt("/")
def events(
    session,
    name: str | None = None,
    id: int | None = None,
    include_previous: bool = False,
):
    forms_stmt = s.table("Event").select('*, responses:"Response" (user_id)')
    if not include_previous:
        forms_stmt = forms_stmt.gt("end_time", datetime.now())
    if name:
        forms_stmt = forms_stmt.like("title", name)
    if id:
        forms_stmt = forms_stmt.eq("id", id)
    forms = forms_stmt.execute().data

    socials = (
        ("github", "https://github.com/Mmesek/mEvents"),
        ("messages-square", "https://discord.com"),
    )
    events = sorted([Event(**f) for f in forms], key=lambda x: x.start_time)

    return (
        fh.Title("Nadchodzące wydarzenia"),
        DivCentered(H1("Nadchodzące wydarzenia")),
        *[
            info_card(
                fh.A(f.title, cls=AT.classic, href=f"/forms/{f.id}"),
                f"{f.start_time.hour}:{f.start_time.minute:0<2}",
                f"{f.end_time.hour}:{f.end_time.minute:0<2}" if f.end_time else "",
                f"{f.start_time.date()}, {f.start_time.strftime('%A')}",
                f.place,
                f.theme,
                f.dresscode,
                f.dresscode_mandatory,
                f.discord_event,
                f.description,
                image=f.image,
                count=len({list(i.values())[0] for i in f.responses}),
                organizer=f.org_name,
                href=f"/forms/{f.id}",
                event_id=f.id,
                logged_in=session.get("email") is not None,
            )
            for f in events
        ],
        Card(
            footer=DivCentered(
                DivLAligned(*[UkIconLink(icon, href=url) for icon, url in socials])
            ),
        ),
    )
