from fasthtml import common as fh
from monsterui.all import (
    AT,
    H1,
    Card,
    DivCentered,
    DivLAligned,
    UkIconLink,
    Theme,
)


from db import s
from generators import info_card
from dataclasses import dataclass
from datetime import datetime


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

    def __post_init__(self):
        self.start_time = datetime.fromisoformat(self.start_time)
        if self.end_time:
            self.end_time = datetime.fromisoformat(self.end_time)


app, rt = fh.fast_app(hdrs=Theme.orange.headers())


@rt("/")
def events():
    forms = s.table("Event").select("*").execute().data

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
                fh.A(f.title, cls=AT.classic, href=f"/forms/{f.form_id}?event={f.id}"),
                f"{f.start_time.hour}:{f.start_time.minute:0<2}",
                f"{f.end_time.hour}:{f.end_time.minute:0<2}",
                f.start_time.date(),
                f.place,
                f.theme,
                f.dresscode,
                f.dresscode_mandatory,
                f.discord_event,
                f.description,
                image=f.image,
            )
            for f in events
        ],
        Card(
            footer=DivCentered(
                DivLAligned(*[UkIconLink(icon, href=url) for icon, url in socials])
            ),
        ),
    )
