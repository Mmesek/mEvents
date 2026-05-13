from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE, with_layout
from src.components.app_factory import make_app
from src.db import Base
from src.modules.tickets import Attendance

rt = make_app("profile")


class Profile(Base):
    user_id: str
    display_name: str

    def render(self, session):
        last_event = Attendance.get_one(
            Attendance.select(session["auth"], 'arrived, left, event:"Event" (title)')
            .eq("user_id", self.user_id)
            .filter("arrived", "is", "not_null")
            .order("arrived", desc=True)
            .limit(1)
        )
        arrived = last_event.arrived.astimezone(TIMEZONE).strftime("%m/%d %H:%M") if last_event.arrived else ""
        left = last_event.left.astimezone(TIMEZONE).strftime("%m/%d %H:%M") if last_event.left else ""
        return mui.DivCentered(
            fh.Div(
                mui.Card(
                    mui.DividerSplit("Ostatnie Wydarzenie"),
                    mui.DivCentered(
                        mui.DivFullySpaced(mui.Small("Od"), mui.Small(last_event.event["title"]), mui.Small("Do")),
                        mui.DivFullySpaced(
                            fh.P(arrived),
                            "->",
                            fh.P(left),
                        ),
                    ),
                    mui.DividerSplit("EXP"),
                    mui.DivCentered(mui.Legend("20/100"), mui.Progress(title="20/100", value=20)),
                    header=mui.DivFullySpaced(
                        self.display_name,
                        fh.Img(src=session.get("picture"), height="64", width="64"),
                    ),
                ),
                mui.Button("Ustawienia"),
                mui.DivCentered(
                    mui.Grid(
                        mui.Button("Zadania"),
                        mui.Button("Poziomy"),
                        mui.Button("Wydarzenia"),
                        mui.Button("Feedback"),
                        cols=4,
                    ),
                ),
            ),
        )


@rt("/")
@with_layout()
def profile(session):
    # p = Profile.get_one(Profile.select(session["auth"]))
    return Profile(session["id"], "Mmesek").render(session)
