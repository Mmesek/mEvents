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
    render_md,
    Grid,
    Input,
    Switch,
    TextArea,
    TextPresets,
    Select,
)
import i18n

from src.components import handle_updating_responses, icon_text, right_icon_text, with_layout, Layout
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
    private: bool = None

    def __post_init__(self):
        if type(self.start_time) is str:
            self.start_time = datetime.fromisoformat(self.start_time)
            if self.end_time:
                self.end_time = datetime.fromisoformat(self.end_time)

    def info_card(
        self,
        count: int = None,
        logged_in: bool = False,
        user_id: str = None,
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
                    fh.A(
                        Button("Sprawdź odpowiedzi", cls=ButtonT.ghost, submit=False),
                        href=f"/responses/{self.id}",
                    )
                    if self.user_id == user_id
                    else None,
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
@with_layout(Layout, "Nadchodzące wydarzenia")
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
    forms_stmt = forms_stmt.eq("id", id) if id else forms_stmt.eq("private", False)
    if user_id:
        forms_stmt = forms_stmt.eq("user_id", user_id)
    forms = forms_stmt.execute().data

    events = sorted([Event(**f) for f in forms], key=lambda x: x.start_time)

    return [
        f.info_card(
            count=len({list(i.values())[0] for i in f.responses}),
            logged_in=session.get("email") is not None,
            user_id=session.get("id"),
        )
        for f in events
    ]


@rt("/create")
def create(session):
    content = DivCentered(
        Card(
            DivCentered(
                H1(
                    Input(
                        id="title",
                        placeholder=i18n.t("events.create.title.name", locale=session.get("locale")),
                        required=True,
                        title=i18n.t("events.create.title.description", locale=session.get("locale")),
                    ),
                ),
                cls="required",
            ),
            Grid(
                icon_text(
                    "clock",
                    Input(
                        type="time",
                        id="start_time",
                        required=True,
                        title=i18n.t("events.create.start.description", locale=session.get("locale")),
                    ),
                    icon_style="required",
                ),
                right_icon_text(
                    "clock-10",
                    Input(
                        type="time",
                        id="end_time",
                        title=i18n.t("events.create.end.description", locale=session.get("locale")),
                    ),
                ),
                icon_text(
                    "calendar",
                    Input(
                        type="date",
                        id="date",
                        required=True,
                        title=i18n.t("events.create.date.description", locale=session.get("locale")),
                    ),
                    icon_style="required",
                ),
                right_icon_text(
                    "pin",
                    Input(
                        id="place",
                        placeholder=i18n.t("events.create.place.name", locale=session.get("locale")),
                        required=True,
                        title=i18n.t("events.create.place.description", locale=session.get("locale")),
                    ),
                    icon_style="required",
                ),
                icon_text(
                    "user",
                    Input(
                        id="org_name",
                        value=s.table("users")
                        .select("display_name")
                        .eq("id", session.get("id"))
                        .execute()
                        .data[0]["display_name"]
                        .title(),
                        title=i18n.t("events.create.org_name.description", locale=session.get("locale")),
                    ),
                ),
                fh.Div(),
                icon_text(
                    "palette",
                    Input(
                        id="theme",
                        placeholder=i18n.t("events.create.theme.name", locale=session.get("locale")),
                        title=i18n.t("events.create.theme.description", locale=session.get("locale")),
                    ),
                ),
                icon_text(
                    "shirt",
                    (
                        Input(
                            id="dresscode",
                            placeholder=i18n.t(
                                "events.create.dresscode.name",
                                locale=session.get("locale"),
                            ),
                            title=i18n.t("events.create.dresscode.description", locale=session.get("locale")),
                        ),
                        Switch(
                            id="dresscode_mandatory",
                            title=i18n.t("events.create.dresscode_mandatory.description", locale=session.get("locale")),
                        ),
                        fh.P(
                            i18n.t("events.create.dresscode_mandatory.name", locale=session.get("locale")),
                            cls=TextPresets.muted_sm,
                        ),
                    ),
                ),
                cols=2,
                cls="gap-1 items-center justify-center",
            ),
            DivCentered(
                TextArea(
                    id="description",
                    placeholder=i18n.t("events.create.description.default", locale=session.get("locale")),
                    title=i18n.t("events.create.description.description", locale=session.get("locale")),
                )
            ),
            Switch(i18n.t("events.create.is_private", locale=session.get("locale")), id="private"),
            fh.Div(
                fh.Label(i18n.t("events.create.select_form", locale=session.get("locale"))),
                fh.Select(
                    *[form_option(f["title"], f["id"]) for f in s.table("Form").select("id, title").execute().data],
                    form_option(i18n.t("events.create.new_form", locale=session.get("locale")), form_id=0),
                    searchable=True,
                    hx_target="#form",
                    hx_swap="innerHTML",
                ),
                fh.Div(id="form"),
            ),
            Select(
                *[
                    form_option(f["title"], f["id"])
                    for f in s.table("Form").select("id, title").ilike("title", "Feedback").execute().data
                ],
                form_option(i18n.t("events.create.no_form", locale=session.get("locale")), None),
                searchable=True,
                placeholder=i18n.t("events.create.select_feedback_form", locale=session.get("locale")),
            ),
            Button(i18n.t("events.create.add.add", locale=session.get("locale")), cls=ButtonT.primary),
        )
    )
    return fh.Container(
        fh.Form(
            DivCentered(
                fh.H1(i18n.t("events.create.add.title", locale=session.get("locale"))),
                i18n.t("events.create.add.description", locale=session.get("locale")),
                DividerLine(),
            ),
            content,
            cls="space-y-3 mt-4",
            hx_post="/events/add",
        )
    )


def form_option(name: str, form_id: int):
    return fh.Option(
        name,
        hx_post=f"/forms/new?form_id={form_id}",
    )


@rt("/add")
def add(session, responses: dict):
    responses = handle_updating_responses(responses)

    try:
        pass  # s.table("Event").upsert([{"user_id": session["id"], **responses}]).execute()
        responses["start_time"] = responses.pop("date") + " " + responses["start_time"]
        return Event(**responses).info_card()

    except Exception as ex:
        return DivCentered(i18n.t("events.create.add.failed", locale=session.get("locale"))), DivRAligned(ex)

    return DivCentered(i18n.t("events.create.add.success", locale=session.get("locale"))), DivRAligned("Test")


@rt("/mine")
def my_events(session):
    return events(session, include_previous=True, user_id=session["id"])
