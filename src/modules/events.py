from datetime import datetime, timedelta
from uuid import UUID

from fasthtml import common as fh
from monsterui import all as mui

from src.components import Layout, handle_updating_responses, icon_text, right_icon_text, with_layout, TIMEZONE
from src.components.app_factory import make_app
from src.components.models import Form
from src.modules.tickets import Attendance
from src.db import Base

rt = make_app("events")

LOCALIZED_NAMES = {
    "Monday": "Poniedziałek",
    "Tuesday": "Wtorek",
    "Wednesday": "Środa",
    "Thursday": "Czwartek",
    "Friday": "Piątek",
    "Saturday": "Sobota",
    "Sunday": "Niedziela",
}


class Event(Base):
    id: int = None
    title: str = None
    description: str | None = None
    form_id: int | None = None
    feedback_form_id: int | None = None
    user_id: UUID = None
    place: str | None = None
    start_time: datetime = None
    end_time: datetime | None = None
    theme: str | None = None
    dresscode: str | None = None
    dresscode_mandatory: bool | None = None
    discord_event: str | None = None
    wrap: str | None = None
    image: str | None = None
    tickets: list[Attendance] = None
    org_name: str | None = None
    private: bool | None = None
    form: Form | None = None

    def __post_init__(self):
        self.start_time = self.start_time.astimezone(TIMEZONE)
        self.end_time = self.end_time.astimezone(TIMEZONE)

    def info_card(self, user_id: str = None):
        if user_id:
            user_id = UUID(user_id)
        if self.dresscode and not self.dresscode_mandatory:
            self.dresscode += " *(Opcjonalnie)*"
        count = len(self.tickets) if self.tickets else None
        companions = sum([i.companions or 0 for i in self.tickets]) if self.tickets else None
        return mui.DivCentered(
            mui.Card(
                fh.Img(
                    src=self.image,
                    loading="lazy",
                    width=1000,
                    height=400,
                    style="max-height: 400px;",
                )
                if self.image
                else None,
                mui.DivCentered(
                    mui.H1(fh.A(self.title, cls=mui.AT.classic, href=f"/forms/{self.id}" if self.id else None))
                ),
                mui.Grid(
                    (
                        right_icon_text(x[0], x[1]) if n % 2 else icon_text(x[0], x[1])
                        for n, x in enumerate(
                            [
                                x
                                for x in (
                                    (
                                        ("clock", self.start_time.strftime("%H:%M")),
                                        ("clock-10", self.end_time.strftime("%H:%M") if self.end_time else ""),
                                        (
                                            "calendar",
                                            f"{self.start_time.date()}, {LOCALIZED_NAMES[self.start_time.strftime('%A')]}",
                                        ),
                                        (
                                            "calendar",
                                            f"{self.end_time.date()}, {LOCALIZED_NAMES[self.end_time.strftime('%A')]}",
                                        )
                                        if self.end_time.date() - self.start_time.date() > timedelta(1)
                                        else None,
                                        ("pin", f"{self.place}"),
                                        (
                                            "users",
                                            f"**Liczba zapisanych**: {count}{(f' + {companions}') if companions else ''}",
                                        )
                                        if count
                                        else None,
                                        ("user", f"**Organizator**: {self.org_name}") if self.org_name else None,
                                        ("palette", f"**Temat Przewodni**: {self.theme}") if self.theme else None,
                                        ("shirt", f"**Styl Ubioru**: {self.dresscode}") if self.dresscode else None,
                                    )
                                )
                                if x
                            ]
                        )
                    ),
                    cols=2,
                    cls="gap-1 items-center justify-center",
                ),
                mui.DivCentered(
                    icon_text(
                        "messages-square",
                        text=f"**[Discord]({self.discord_event})**",
                    )
                )
                if self.discord_event
                else None,
                # mui.DivCentered(icon_text("", text=f"**[Facebook]({self.facebook_event})**")) if self.facebook_event else None,
                mui.DivCentered(mui.render_md(self.description)) if self.description else None,
                mui.DivRAligned(mui.DivHStacked(*self.event_buttons(user_id))),
                body_cls="space-y-0",
                style="max-width: 1000px; min-width: 35%",
            )
        )

    @property
    def event_started(self):
        return self.start_time < datetime.now(TIMEZONE)

    def render_button_guests(self):
        return mui.Button(
            "Lista gości",
            cls=mui.ButtonT.ghost,
            submit=False,
            hx_target=f"#guestlist_{self.id}",
            hx_get=f"/events/guests?event_id={self.id}",
        )

    def render_button_form_responses(self):
        return (
            fh.A(
                mui.Button("Sprawdź Feedback", cls=mui.ButtonT.ghost, submit=False),
                href=f"/responses/{self.id}?feedback=true",
            )
            if self.event_started
            else fh.A(
                mui.Button("Sprawdź odpowiedzi", cls=mui.ButtonT.ghost, submit=False),
                href=f"/responses/{self.id}",
            )
        )

    def event_buttons(self, user_id: UUID):
        buttons = []
        if self.user_id and self.user_id == user_id:
            buttons.append(self.render_button_form_responses())
            if self.event_started:
                buttons.append(
                    fh.A(mui.Button("Obecność", cls=mui.ButtonT.ghost), href=f"/tickets/attendance/{self.id}")
                )
        if is_guest := any(user_id == x.user_id for x in self.tickets) if self.tickets else None:
            buttons.append(fh.A(mui.Button("Przygotowania", cls=mui.ButtonT.ghost), href=f"/contributions/{self.id}"))
        if user_id:
            buttons.append(mui.DivLAligned(self.render_button_guests(), id=f"guestlist_{self.id}"))
        if self.id:
            if not self.event_started:
                buttons.append(
                    fh.A(mui.Button("Weź udział", cls=mui.ButtonT.ghost, submit=False), href=f"/forms/{self.id}")
                )
            elif is_guest:
                buttons.append(
                    fh.A(
                        mui.Button("Udziel feedbacku", cls=mui.ButtonT.ghost, submit=False),
                        href=f"/forms/feedback/{self.id}",
                    )
                )
        return buttons


@rt("/guests")
def list_guests(session, event_id: str):
    names = (
        Attendance.select(session["auth"], "*, ...users!Attendance_user_id_fkey (display_name)")
        .eq("event_id", event_id)
        .eq("users.event_id", event_id)
        .filter("withdrew", "is", "null")
        .order("created_at")
        .execute()
        .data
    )
    return mui.DivCentered(fh.Ol(*[fh.Li(i["display_name"]) for i in names], cls=mui.ListT.decimal))


def open_graph(title, description, thumbnail_url):
    return (
        fh.Meta(property="og:site_name", content="Mistyczne Wydarzenia Ognia i Popiołu"),
        fh.Meta(property="og:title", content=title),
        fh.Meta(property="og:description", content=description),
        fh.Meta(property="og:image", content=thumbnail_url),
        fh.Meta(property="og:type", content="article"),
        fh.Meta(name="twitter:card", content="summary"),
        fh.Meta(name="twitter:title", content=title),
        fh.Meta(name="twitter:description", content=description),
        fh.Meta(name="twitter:image", content=thumbnail_url),
    )


@rt("/")
@with_layout(Layout, "Nadchodzące wydarzenia")
def events(
    session,
    name: str | None = None,
    id: int | None = None,
    include_previous: bool = False,
    user_id: str = None,
):
    forms_stmt = Event.select(None, '*, tickets:"Attendance" (user_id, companions)').filter(
        "tickets.withdrew", "is", "null"
    )

    if not include_previous and not id:
        forms_stmt = forms_stmt.gt("end_time", datetime.now(TIMEZONE))
    if name:
        forms_stmt = forms_stmt.like("title", name)
    forms_stmt = forms_stmt.eq("id", id) if id else forms_stmt.eq("private", False)
    if user_id:
        forms_stmt = forms_stmt.eq("user_id", user_id)
    events = sorted(Event.get(forms_stmt), key=lambda x: x.start_time)

    return *[f.info_card(user_id=session.get("id")) for f in events], *open_graph(
        events[0].title, events[0].description, events[0].image
    )


@rt("/create")
def create(session, t):
    content = mui.DivCentered(
        mui.Card(
            mui.DivCentered(
                mui.H1(
                    mui.Input(
                        id="title",
                        placeholder=t("events.create.title.name"),
                        required=True,
                        title=t("events.create.title.description"),
                    ),
                ),
                cls="required",
            ),
            mui.Grid(
                icon_text(
                    "clock",
                    mui.Input(
                        type="time",
                        id="start_time",
                        required=True,
                        title=t("events.create.start.description"),
                    ),
                    icon_style="required",
                ),
                right_icon_text(
                    "clock-10",
                    mui.Input(
                        type="time",
                        id="end_time",
                        title=t("events.create.end.description"),
                    ),
                ),
                icon_text(
                    "calendar",
                    mui.Input(
                        type="date",
                        id="start_date",
                        required=True,
                        title=t("events.create.date.description"),
                    ),
                    icon_style="required",
                ),
                icon_text(
                    "calendar",
                    mui.Input(
                        type="date",
                        id="end_date",
                        required=True,
                        title=t("events.create.date.description"),
                    ),
                    icon_style="required",
                ),
                right_icon_text(
                    "pin",
                    mui.Input(
                        id="place",
                        placeholder=t("events.create.place.name"),
                        required=True,
                        title=t("events.create.place.description"),
                    ),
                    icon_style="required",
                ),
                icon_text(
                    "user",
                    mui.Input(
                        id="org_name",
                        value=session["display_name"].title(),
                        title=t("events.create.org_name.description"),
                    ),
                ),
                icon_text(
                    "palette",
                    mui.Input(
                        id="theme",
                        placeholder=t("events.create.theme.name"),
                        title=t("events.create.theme.description"),
                    ),
                ),
                icon_text(
                    "shirt",
                    (
                        mui.Input(
                            id="dresscode",
                            placeholder=t("events.create.dresscode.name"),
                            title=t("events.create.dresscode.description"),
                        ),
                        mui.Switch(
                            id="dresscode_mandatory",
                            title=t("events.create.dresscode_mandatory.description"),
                        ),
                        fh.P(
                            t("events.create.dresscode_mandatory.name"),
                            cls=mui.TextPresets.muted_sm,
                        ),
                    ),
                ),
                cols=2,
                cls="gap-1 items-center justify-center",
            ),
            mui.DivCentered(
                mui.TextArea(
                    id="description",
                    placeholder=t("events.create.description.default"),
                    title=t("events.create.description.description"),
                )
            ),
            mui.Switch(t("events.create.is_private"), id="private"),
            fh.Div(
                fh.Label(t("events.create.select_form")),
                fh.Select(
                    *[
                        form_option(f["title"], f["id"])
                        for f in Form.select(session["auth"], "id, title").execute().data
                    ],
                    form_option(t("events.create.new_form"), form_id=None),
                    id="form_id",
                    searchable=True,
                    hx_target="#form",
                    hx_swap="innerHTML",
                ),
                fh.Div(id="form"),
            ),
            mui.Select(
                *[
                    form_option(f["title"], f["id"])
                    for f in Form.select(session["auth"], "id, title").ilike("title", "Feedback").execute().data
                ],
                form_option(t("events.create.no_form"), None),
                searchable=True,
                placeholder=t("events.create.select_feedback_form"),
                id="feedback_form_id",
            ),
            mui.Button(t("events.create.add.add"), cls=mui.ButtonT.primary),
        )
    )
    return mui.Container(
        fh.Form(
            mui.DivCentered(
                fh.H1(t("events.create.add.title")),
                t("events.create.add.description"),
                mui.DividerLine(),
            ),
            content,
            cls="space-y-3 mt-4",
            hx_post="/events/add",
        )
    )


def form_option(name: str, form_id: int):
    return fh.Option(name, hx_post=f"/forms/new?form_id={form_id}", value=form_id)


@rt
def add(session, responses: dict, *, t=None):
    responses = handle_updating_responses(responses)

    try:
        responses["start_time"] = responses.pop("start_date") + "T" + responses["start_time"] + ":00"
        responses["end_time"] = responses.pop("end_date") + "T" + responses["end_time"] + ":00"
        responses["dresscode_mandatory"] = responses.get("dresscode_mandatory", False) == "on"
        Event.table(session["auth"]).upsert([{"user_id": session["id"], **responses}]).execute()
        responses["form_id"] = int(responses.get("form_id", 0))
        responses["feedback_form_id"] = int(responses.get("feedback_form_id", 0))

        return Event.from_dict(responses).info_card()

    except Exception as ex:
        return mui.DivCentered(t("events.create.add.failed")), mui.DivRAligned(ex)

    return mui.DivCentered(t("events.create.add.success")), mui.DivRAligned("Test")


@rt
def mine(session):
    return events(session, include_previous=True, user_id=session["id"])
