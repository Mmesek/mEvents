from dataclasses import dataclass
from datetime import datetime
from inspect import get_annotations

from fasthtml import common as fh
from monsterui.all import (
    AT,
    H1,
    Button,
    ButtonT,
    Card,
    DivCentered,
    DividerLine,
    DivLAligned,
    DivRAligned,
    UkIconLink,
)
from src.components import handle_updating_responses
from src.components.headers import HEADERS
from src.db import s
from src.generators import QuestionTypes, info_card


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
    user_id: str = None,
):
    forms_stmt = s.table("Event").select('*, responses:"Response" (user_id)')
    if not include_previous:
        forms_stmt = forms_stmt.gt("end_time", datetime.now())
    if name:
        forms_stmt = forms_stmt.like("title", name)
    if id:
        forms_stmt = forms_stmt.eq("id", id)
    if user_id:
        forms_stmt = forms_stmt.eq("user_id", user_id)
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


@dataclass
class EventForm:
    title: str = ("Title", "Title of the event")
    description: str | None = ("Description", None)
    place: str = ("Place", "Where is the event happening?")
    start_time: datetime = ("Start", "When is the start?")
    end_time: datetime | None = ("End", "When is it ending?")
    theme: str | None = ("Theme", "Temat Przewodni")
    dresscode: str | None = ("Dresscode", "Jaki dress-code jest wymagany?")
    dresscode_mandatory: bool | None = ("Czy Dresscode jest wymagany?", None)
    image: str | None = ("Grafika", None)
    org_name: str | None = ("Wyświetlana nazwa organizatora", None)


@rt("/create")
def create(session):
    display_name = (
        s.table("users")
        .select("display_name")
        .eq("id", session.get("id"))
        .execute()
        .data[0]["display_name"]
    )
    defaults = {
        "title": "Nazwa Wydarzenia",
        "description": "Wydarzenie poświęcone wydarzeniu wydarzeniowemu",
        "place": "Miejsce",
        "theme": "Średniowieczny",
        "dresscode": "Szlachetny",
        "org_name": display_name.title(),
    }
    content = []
    for k, v in get_annotations(EventForm).items():
        if hasattr(v, "__args__"):
            v = v.__args__[0]
            optional = True
        else:
            optional = False
        _type = QuestionTypes.get(str(v)) or QuestionTypes.get(str(str))
        content.append(
            _type(
                getattr(EventForm, k)[0],
                question_id=k,
                description=getattr(EventForm, k)[1] or None,
                placeholder=defaults.get(k),
                required=not optional,
            )
        )
    content.append(Button("Dodaj", cls=ButtonT.primary))
    return fh.Container(
        fh.Form(
            DivCentered(
                fh.H1("Nowe Wydarzenie"),
                "Opis",
                DividerLine(),
            ),
            *content,
            cls="space-y-3 mt-4",
            hx_post="/events/add",
        )
    )


@rt("/add")
def add(session, responses: dict):
    responses = handle_updating_responses(responses)

    try:
        pass  # s.table("Event").upsert([{"user_id": session["id"], **responses}]).execute()
    except:
        return DivCentered(
            "Coś poszło nie tak... odśwież stronę i wprowadź odpowiedzi ponownie."
        )

    return DivCentered("Dodano Wydarzenie!"), DivRAligned("Test")


@rt("/mine")
def my_events(session):
    return events(session, include_previous=True, user_id=session["id"])
