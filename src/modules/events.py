from datetime import datetime, timedelta
from uuid import UUID

from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE, Layout, icon_text, open_graph, with_layout, back_to_main
from src.components.app_factory import make_app
from src.models.events import Event as Events, Attendance
from src.components.info import MetaInfo
from src import components as mu

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


class Event(Events):
    def info_card(self, user_id: str = None):
        if user_id:
            user_id = UUID(user_id)
        if self.dresscode and not self.dresscode_mandatory:
            self.dresscode += " *(Opcjonalnie)*"
        count = len(self.tickets) if self.tickets else None
        companions = sum([i.companions or 0 for i in self.tickets]) if self.tickets else None
        return mui.Card(
            fh.Img(
                src=self.image,
                loading="lazy",
                width=1000,
                height=400,
                style="max-height: 400px; border-radius: 1.5em",
            )
            if self.image
            else None,
            mui.DivCentered(
                mui.H1(fh.A(self.title, cls=mui.AT.classic, href=f"/forms/{self.id}" if self.id else None))
            ),
            MetaInfo(
                self.start_time.strftime("%H:%M"),
                self.end_time.strftime("%H:%M") if self.end_time else None,
                f"{self.start_time.date()}, {LOCALIZED_NAMES[self.start_time.strftime('%A')]}",
                f"{self.end_time.date()}, {LOCALIZED_NAMES[self.end_time.strftime('%A')]}"
                if self.end_time.date() - self.start_time.date() > timedelta(1)
                else None,
                self.place,
                f"{count} + {companions}" if companions else count,
                self.org_name,
                self.theme,
                self.dresscode,
            ).render(),
            mui.DivCentered(
                icon_text(
                    "messages-square",
                    text=f"**[Discord]({self.discord_event})**",
                )
            )
            if self.discord_event
            else None,
            # mui.DivCentered(icon_text("", text=f"**[Facebook]({self.facebook_event})**")) if self.facebook_event else None,
            (
                fh.Hr(cls="orange-hr", style="--secondary: #F59E0B; height: 1px;"),
                mui.DivCentered(mui.render_md(self.description)),
            )
            if self.description
            else None,
            fh.Hr(cls="orange-hr", style="--secondary: #F59E0B; height: 1px;"),
            mui.DivRAligned(mui.DivHStacked(*self.event_buttons(user_id))),
            body_cls="space-y-0",
            style="max-width: 1000px; min-width: 35%; border-radius: 1.5em",
        )

    def render_button_guests(self):
        return mu.Button(
            "Lista gości",
            cls=mu.ButtonT.secondary,
            submit=False,
            hx_target=f"#guestlist_{self.id}",
            hx_get=f"/events/guests?event_id={self.id}",
        )

    def render_button_form_responses(self):
        return (
            fh.A(
                mu.Button("Sprawdź Feedback", cls=mu.ButtonT.secondary, submit=False),
                href=f"/responses/{self.id}?feedback=true",
            )
            if self.event_started
            else fh.A(
                mu.Button("Sprawdź odpowiedzi", cls=mu.ButtonT.secondary, submit=False),
                href=f"/responses/{self.id}",
            )
        )

    def event_buttons(self, user_id: UUID):
        buttons = []
        if self.user_id and self.user_id == user_id:
            buttons.append(self.render_button_form_responses())
            if self.event_started:
                buttons.append(
                    fh.A(mu.Button("Obecność", cls=mu.ButtonT.secondary), href=f"/tickets/attendance/{self.id}")
                )
            buttons.append(
                mui.DivLAligned(
                    mu.Button(
                        "E-Maile",
                        hx_target=f"#guestemails_{self.id}",
                        hx_get=f"/tickets/attendance/{self.id}/emails",
                        cls=mu.ButtonT.secondary,
                    ),
                    id=f"guestemails_{self.id}",
                )
            )
        if is_guest := any(user_id == x.user_id for x in self.tickets) if self.tickets else None:
            buttons.append(fh.A(mu.Button("Przygotowania", cls=mu.ButtonT.secondary), href=f"/contributions/{self.id}"))
        if user_id:
            buttons.append(mui.DivLAligned(self.render_button_guests(), id=f"guestlist_{self.id}"))
        if self.id:
            if not self.event_started:
                buttons.append(
                    fh.A(mu.Button("Weź udział", cls=mu.ButtonT.primary, submit=False), href=f"/forms/{self.id}")
                )
            elif is_guest:
                buttons.append(
                    fh.A(
                        mu.Button("Udziel feedbacku", cls=mu.ButtonT.primary, submit=False),
                        href=f"/forms/feedback/{self.id}",
                    )
                )
        return buttons


@rt
def guests(session, event_id: str):
    names = Attendance(event_id).event_guests(session)
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
    try:
        meta = open_graph(events[0].title, events[0].description, events[0].image)
    except IndexError:
        meta = []

    return *([f.info_card(user_id=session.get("id")) for f in events] or [back_to_main()]), *meta


@rt
def mine(session):
    return events(session=session, include_previous=True, user_id=session["id"])
