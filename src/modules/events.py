from datetime import datetime, timedelta
from uuid import UUID

import i18n
from fasthtml import common as fh
from monsterui import all as mui

from src.components import Layout, handle_updating_responses, icon_text, right_icon_text, with_layout, TIMEZONE
from src.components.app_factory import make_app
from src.components.models import Form, Response
from src.db import Base, s

rt = make_app("events")


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
    responses: list[Response] = None
    org_name: str | None = None
    private: bool | None = None
    form: dict | None = None

    def __post_init__(self):
        self.start_time = self.start_time.astimezone(TIMEZONE)
        self.end_time = self.end_time.astimezone(TIMEZONE)

    def info_card(self, user_id: str = None):
        if user_id:
            user_id = UUID(user_id)
        if self.dresscode and not self.dresscode_mandatory:
            self.dresscode += " *(Opcjonalnie)*"
        count = len({i.user_id for i in self.responses}) if self.responses else None
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
                                        ("calendar", f"{self.start_time.date()}, {self.start_time.strftime('%A')}"),
                                        ("calendar", f"{self.end_time.date()}, {self.end_time.strftime('%A')}")
                                        if self.end_time.date() - self.start_time.date() > timedelta(1)
                                        else None,
                                        ("pin", f"{self.place}"),
                                        ("users", f"**Liczba zapisanych**: {count}") if count else None,
                                        ("user", f"**Organizator**: {self.org_name}") if self.org_name else None,
                                        ("palette", f"**Temat Przewodni**: {self.theme}") if self.theme else None,
                                        ("shirt", f"**Dresscode**: {self.dresscode}") if self.dresscode else None,
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
                mui.DivCentered(mui.render_md(self.description)) if self.description else None,
                mui.DivRAligned(mui.Grid(*self.event_buttons(user_id))),
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
        if is_guest := any(user_id == x.user_id for x in self.responses) if self.responses else None:
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
        s.auth(session["auth"])
        .table("users")
        .select("display_name")
        .eq("event_id", event_id)
        .order("timestamp")
        .execute()
        .data
    )
    return mui.DivCentered(fh.Ol(*[fh.Li(i["display_name"]) for i in names], cls=mui.ListT.decimal))


@rt("/")
@with_layout(Layout, "Nadchodzące wydarzenia")
def events(
    session,
    name: str | None = None,
    id: int | None = None,
    include_previous: bool = False,
    user_id: str = None,
):
    forms_stmt = Event.table().select('*, responses:"Response" (user_id)')
    if not include_previous:
        forms_stmt = forms_stmt.gt("end_time", datetime.now(TIMEZONE))
    if name:
        forms_stmt = forms_stmt.like("title", name)
    forms_stmt = forms_stmt.eq("id", id) if id else forms_stmt.eq("private", False)
    if user_id:
        forms_stmt = forms_stmt.eq("user_id", user_id)

    return [f.info_card(user_id=session.get("id")) for f in sorted(Event.get(forms_stmt), key=lambda x: x.start_time)]


@rt("/create")
def create(session):
    content = mui.DivCentered(
        mui.Card(
            mui.DivCentered(
                mui.H1(
                    mui.Input(
                        id="title",
                        placeholder=i18n.t("events.create.title.name", locale=session.get("locale")),
                        required=True,
                        title=i18n.t("events.create.title.description", locale=session.get("locale")),
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
                        title=i18n.t("events.create.start.description", locale=session.get("locale")),
                    ),
                    icon_style="required",
                ),
                right_icon_text(
                    "clock-10",
                    mui.Input(
                        type="time",
                        id="end_time",
                        title=i18n.t("events.create.end.description", locale=session.get("locale")),
                    ),
                ),
                icon_text(
                    "calendar",
                    mui.Input(
                        type="date",
                        id="start_date",
                        required=True,
                        title=i18n.t("events.create.date.description", locale=session.get("locale")),
                    ),
                    icon_style="required",
                ),
                icon_text(
                    "calendar",
                    mui.Input(
                        type="date",
                        id="end_date",
                        required=True,
                        title=i18n.t("events.create.date.description", locale=session.get("locale")),
                    ),
                    icon_style="required",
                ),
                right_icon_text(
                    "pin",
                    mui.Input(
                        id="place",
                        placeholder=i18n.t("events.create.place.name", locale=session.get("locale")),
                        required=True,
                        title=i18n.t("events.create.place.description", locale=session.get("locale")),
                    ),
                    icon_style="required",
                ),
                icon_text(
                    "user",
                    mui.Input(
                        id="org_name",
                        value=session["display_name"].title(),
                        title=i18n.t("events.create.org_name.description", locale=session.get("locale")),
                    ),
                ),
                fh.Div(),
                icon_text(
                    "palette",
                    mui.Input(
                        id="theme",
                        placeholder=i18n.t("events.create.theme.name", locale=session.get("locale")),
                        title=i18n.t("events.create.theme.description", locale=session.get("locale")),
                    ),
                ),
                icon_text(
                    "shirt",
                    (
                        mui.Input(
                            id="dresscode",
                            placeholder=i18n.t(
                                "events.create.dresscode.name",
                                locale=session.get("locale"),
                            ),
                            title=i18n.t("events.create.dresscode.description", locale=session.get("locale")),
                        ),
                        mui.Switch(
                            id="dresscode_mandatory",
                            title=i18n.t("events.create.dresscode_mandatory.description", locale=session.get("locale")),
                        ),
                        fh.P(
                            i18n.t("events.create.dresscode_mandatory.name", locale=session.get("locale")),
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
                    placeholder=i18n.t("events.create.description.default", locale=session.get("locale")),
                    title=i18n.t("events.create.description.description", locale=session.get("locale")),
                )
            ),
            mui.Switch(i18n.t("events.create.is_private", locale=session.get("locale")), id="private"),
            fh.Div(
                fh.Label(i18n.t("events.create.select_form", locale=session.get("locale"))),
                fh.Select(
                    *[
                        form_option(f["title"], f["id"])
                        for f in Form.select(session["auth"], "id, title").execute().data
                    ],
                    form_option(i18n.t("events.create.new_form", locale=session.get("locale")), form_id=0),
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
                form_option(i18n.t("events.create.no_form", locale=session.get("locale")), None),
                searchable=True,
                placeholder=i18n.t("events.create.select_feedback_form", locale=session.get("locale")),
            ),
            mui.Button(i18n.t("events.create.add.add", locale=session.get("locale")), cls=mui.ButtonT.primary),
        )
    )
    return fh.Container(
        fh.Form(
            mui.DivCentered(
                fh.H1(i18n.t("events.create.add.title", locale=session.get("locale"))),
                i18n.t("events.create.add.description", locale=session.get("locale")),
                mui.DividerLine(),
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
        responses["start_time"] = responses.pop("start_date") + " " + responses["start_time"]
        responses["end_time"] = responses.pop("end_date") + " " + responses["end_time"]
        responses["dresscode_mandatory"] = responses.get("dresscode_mandatory", False)
        Event.table(session["auth"]).upsert([{"user_id": session["id"], **responses}]).execute()
        return Event(**responses).info_card()

    except Exception as ex:
        return mui.DivCentered(i18n.t("events.create.add.failed", locale=session.get("locale"))), mui.DivRAligned(ex)

    return mui.DivCentered(i18n.t("events.create.add.success", locale=session.get("locale"))), mui.DivRAligned("Test")


@rt("/mine")
def my_events(session):
    return events(session, include_previous=True, user_id=session["id"])
