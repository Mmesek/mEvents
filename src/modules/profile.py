from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE, with_layout
from src.components.app_factory import make_app
from src.db import Base, supa
from src.modules.tickets import Attendance
from src.modules.login import PROVIDERS
from src.models.forms import Form
from src import components as mu

rt = make_app("profile")


class Profile(Base):
    user_id: str
    display_name: str

    def edit(self, session):
        r = supa.auth.get_user(session["auth"])
        identities = {i.provider: i.identity_data for i in r.user.identities}
        form = Form.get_one(
            Form.select(
                session["auth"],
                '*, questions:"Form_Questions" (order, required, question:"Question" (*, options:"Question_Options" (id, value), answer:"Response" (value)))',
            )
            .eq("id", 21)
            .eq("questions.question.answer.event_id", 0)
            .eq("questions.question.answer.user_id", session["id"])
        )

        return mui.DivCentered(
            mui.Card(
                form.render(0),
                mui.DividerSplit("Połączone konta"),
                mui.Grid(
                    mu.Button("", PROVIDERS.get(k.title(), k.title()), " - ", v.get("full_name"), disabled=True)
                    for k, v in identities.items()
                ),
            )
        )

    def render(self, session):
        last_event = Attendance(user_id=self.user_id).last_event(session)
        arrived = last_event.arrived.astimezone(TIMEZONE).strftime("%m/%d %H:%M") if last_event.arrived else ""
        left = last_event.left.astimezone(TIMEZONE).strftime("%m/%d %H:%M") if last_event.left else ""
        return mui.DivCentered(
            fh.Div(
                mui.Card(
                    mui.DividerSplit("Ostatnie Wydarzenie"),
                    (
                        mui.DivCentered(
                            mui.DivFullySpaced(mui.Small("Od"), mui.Small(last_event.event["title"]), mui.Small("Do")),
                            mui.DivFullySpaced(
                                fh.P(arrived),
                                "->",
                                fh.P(left),
                            ),
                        )
                    )
                    if last_event.event
                    else None,
                    mui.DividerSplit("EXP"),
                    mui.DivCentered(mui.Legend("0/100"), mui.Progress(title="0/100", value=0)),
                    header=mui.DivFullySpaced(
                        self.display_name,
                        fh.Img(src=session.get("picture"), height="64", width="64"),
                    ),
                ),
                fh.A(mu.Button("Ustawienia", cls=mu.ButtonT.block + mu.ButtonT.accent), href="/profile/settings"),
                mui.DivCentered(
                    mui.Card(
                        mui.DividerSplit("Przejdź do"),
                        mui.Grid(
                            mu.LinkNeutral("/events", "Wydarzeń"),
                            mu.LinkNeutral("/feedback", "Feedbacku", disabled=True),
                            cols=2,
                        ),
                        mui.DividerSplit("Zarządzaj"),
                        mui.Grid(
                            mu.LinkNeutral("/quests", "Zadania", disabled=True),
                            mu.LinkNeutral("/profile/levels", "Poziomy", disabled=True),
                            mu.LinkNeutral("/characters", "Postać", disabled=True),
                            mu.LinkNeutral("/items", "Ekwipunek", disabled=True),
                            cols=4,
                        ),
                        mui.DividerSplit("Moje..."),
                        mui.Grid(
                            mu.LinkNeutral("/events/mine", "Wydarzenia", cls=mu.ButtonT.neutral),
                            mu.LinkNeutral("/contributions", "Deklaracje", disabled=True),
                            mu.LinkNeutral("/tickets", "Bilety", disabled=True),
                            cols=3,
                        ),
                    ),
                ),
            ),
        )


@rt("/")
@with_layout()
def profile(session):
    # p = Profile.get_one(Profile.select(session["auth"]))
    return Profile(session["id"], session["display_name"]).render(session)


@rt
@with_layout()
def settings(session):
    # p = Profile.get_one(Profile.select(session["auth"]))
    return Profile(session["id"], session["display_name"]).edit(session)
