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
    render_md,
    Grid,
)
import i18n

from src.components import handle_updating_responses, icon_text, right_icon_text
from src.components.headers import HEADERS
from src.db import s
from src.generators import QuestionTypes, guests
from src.beforeware import beforeware, translations


@dataclass
class Event:
    id: int = None
    title: str = None
    description: str = None
    form_id: int = None
    feedback_form_id: int = None
    user_id: str = None
    place: str = None
    start_time: datetime = None
    end_time: datetime | None = None
    theme: str | None = None
    dresscode: str | None = None
    dresscode_mandatory: bool = None
    discord_event: str | None = None
    wrap: str = None
    image: str = None
    responses: list[dict] = None
    org_name: str = None

    def __post_init__(self):
        self.start_time = datetime.fromisoformat(self.start_time)
        if self.end_time:
            self.end_time = datetime.fromisoformat(self.end_time)

    def info_card(
        self,
        count: int = None,
        logged_in: bool = False,
    ):
        if self.dresscode and not self.dresscode_mandatory:
            self.dresscode += " *(Opcjonalnie)*"
        align = right_icon_text if count else icon_text
        return DivCentered(
            Card(
                fh.Img(
                    src=self.image,
                    loading="lazy",
                    width=1000,
                    height=400,
                    style="max-height: 400px;",
                )
                if self.image
                else None,
                DivCentered(H1(fh.A(self.title, cls=AT.classic, href=f"/forms/{self.id}" if self.id else None))),
                Grid(
                    icon_text("clock", self.start_time.strftime("%H:%M")),
                    right_icon_text("clock-10", self.end_time.strftime("%H:%M") if self.end_time else ""),
                    cols=2,
                    cls="gap-1 items-center justify-center",
                ),
                Grid(
                    icon_text("calendar", f"{self.start_time.date()}, {self.start_time.strftime('%A')}"),
                    right_icon_text("pin", f"{self.place}"),
                    (icon_text("users", f"**Liczba zapisanych**: {count}")) if count else None,
                    (align("user", f"**Organizator**: {self.org_name}")) if self.org_name else None,  # s.table("users")
                    # .select("display_name")
                    # .eq("id", self.user_id)
                    # .execute()
                    # .data[0]["display_name"],
                    cols=2,
                    cls="gap-1",
                ),
                (icon_text("palette", f"**Temat Przewodni**: {self.theme}")) if self.theme else None,
                (icon_text("shirt", f"**Dresscode**: {self.dresscode}")) if self.dresscode else None,
                DivCentered(
                    icon_text(
                        "messages-square",
                        text=f"**[Discord]({self.discord_event})**",
                    )
                )
                if self.discord_event
                else None,
                DivCentered(render_md(self.description)) if self.description else None,
                DivRAligned(
                    DivLAligned(
                        guests(self.id, target=f"guestlist_{self.id}"),
                        id=f"guestlist_{self.id}",
                    )
                    if logged_in
                    else None,
                    fh.A(
                        Button("Weź udział", cls=ButtonT.ghost, submit=False),
                        href=f"/forms/{self.id}" if self.id else None,
                    ),
                ),
                body_cls="space-y-0",
                style="max-width: 1000px; min-width: 35%",
            )
        )


app, rt = fh.fast_app(hdrs=HEADERS, before=[beforeware, translations])


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
            f.info_card(
                count=len({list(i.values())[0] for i in f.responses}),
                logged_in=session.get("email") is not None,
            )
            for f in events
        ],
        Card(
            footer=DivCentered(DivLAligned(*[UkIconLink(icon, href=url) for icon, url in socials])),
        ),
    )


@dataclass
class EventForm:
    title: str
    description: str | None
    place: str
    start_time: datetime
    end_time: datetime | None
    theme: str | None
    dresscode: str | None
    dresscode_mandatory: bool | None
    image: str | None
    org_name: str | None


@rt("/create")
def create(session):
    session["locale"] = "pl"
    defaults = {
        k: i18n.t(f"events.create.{k}.default", locale=session.get("locale")) for k in EventForm.__annotations__
    }
    defaults["org_name"] = (
        s.table("users").select("display_name").eq("id", session.get("id")).execute().data[0]["display_name"]
    ).title()
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
                i18n.t(f"events.create.{k}.name", locale=session.get("locale")),
                question_id=k,
                description=i18n.t(f"events.create.{k}.description", locale=session.get("locale")),
                placeholder=defaults.get(k),
                required=not optional,
            )
        )
    content.append(Button(i18n.t("events.create.add.add", locale=session.get("locale")), cls=ButtonT.primary))
    return fh.Container(
        fh.Form(
            DivCentered(
                fh.H1(i18n.t("events.create.add.title", locale=session.get("locale"))),
                i18n.t("events.create.add.description", locale=session.get("locale")),
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
        return Event(**responses).info_card()

    except Exception as ex:
        return DivCentered(i18n.t("events.create.add.failed", locale=session.get("locale"))), DivRAligned(ex)

    return DivCentered(i18n.t("events.create.add.success", locale=session.get("locale"))), DivRAligned("Test")


@rt("/mine")
def my_events(session):
    return events(session, include_previous=True, user_id=session["id"])
