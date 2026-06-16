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
                style="max-height: 400px; border-radius: 1.5em; object-fit: cover",
            )
            if self.image
            else None,
            mui.DivCentered(
                fh.Div(
                    mu.CopyToClipboard(f"https://mms-events.vercel.app/events?id={self.id}"),
                    mui.H1(fh.A(self.title, cls=mui.AT.classic, href=f"/forms/{self.id}" if self.id else None)),
                    cls="flex",
                ),
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
            # fh.Hr(cls="orange-hr", style="--secondary: #F59E0B; height: 1px;"),
            mui.DivRAligned(mui.Grid(*self.event_buttons(user_id), cols_min=2, cols_max=6)),
            body_cls="space-y-0",
            style="max-width: 1000px; min-width: 35%; border-radius: 1.5em",
        )

    def render_button_guests(self):
        return mu.ReplaceButton("Lista Gości", f"/events/guests?event_id={self.id}", f"guestlist_{self.id}")

    def render_button_form_responses(self):
        return mu.LinkSecondary(
            f"/responses/{self.id}{'?feedback=true' if self.event_started else ''}",
            f"Sprawdź {'Feedback' if self.event_started else 'odpowiedzi'}",
        )

    def event_buttons(self, user_id: UUID):
        buttons = []
        if self.user_id and self.user_id == user_id:
            buttons.append(self.render_button_form_responses())
            if self.event_started:
                buttons.append(mu.LinkSecondary(f"/tickets/attendance/{self.id}", "Obecność"))
            buttons.append(
                mu.ReplaceButton("E-Maile", f"/tickets/attendance/{self.id}/emails", f"guestemails_{self.id}")
            )
        if user_id:
            buttons.append(self.render_button_guests())
        if is_guest := any(str(user_id) == x.user_id for x in self.tickets) if self.tickets else None:
            buttons.append(mu.LinkSecondary(f"/contributions/{self.id}", "Przygotowania"))
        if self.id:
            if not self.event_started:
                if is_guest:
                    buttons.append(mu.LinkSecondary(f"/forms/{self.id}", "Edytuj odpowiedzi"))
                    buttons.append(
                        mu.ReplaceButton(
                            "Zrezygnuj",
                            f"/events/withdraw?event_id={self.id}",
                            f"withdraw-{self.id}",
                            cls=mu.ButtonT.error,
                        )
                    )
                else:
                    buttons.append(mu.LinkPrimary(f"/forms/{self.id}", "Weź udział"))
            elif is_guest:
                buttons.append(mu.LinkPrimary(f"/forms/feedback/{self.id}", "Udziel feedbacku"))
        return buttons


@rt
def withdraw(session, event_id: str):
    Attendance(event_id=event_id, user_id=session["id"], withdrew=datetime.now(TIMEZONE).isoformat()).upsert(
        session["auth"]
    )
    return mu.LinkPrimary(f"/forms/{event_id}", "Weź udział")


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
