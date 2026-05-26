from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE, with_layout
from src.components.app_factory import make_app
from src.db import Base, supa
from src.modules.tickets import Attendance
from src.modules.login import PROVIDERS

rt = make_app("profile")


class Profile(Base):
    user_id: str
    display_name: str

    def edit(self, session):
        r = supa.auth.get_user(session["auth"])
        identities = {i.provider: i.identity_data for i in r.user.identities}
        return mui.DivCentered(
            mui.Form(
                mui.Card(
                    mui.LabelInput(
                        "Imię",
                        placeholder="Imię N",
                        value=self.display_name,
                        title="Nazwa pod którą można cię rozpoznać",
                    ),
                    mui.LabelInput(
                        "Podłączony e-mail",
                        placeholder="email@example.com",
                        value=session["email"],
                        title="E-mail do kontaktu",
                        disabled=True,
                    ),
                    mui.Switch(
                        "Zgoda na przetwarzanie wizerunku",
                        title="W celu publikacji na mediach społecznościowych",
                        disabled=True,
                    ),
                    mui.LabelInput(
                        "Alergie",
                        title="Załączone do zapisów na wydarzenia które zawierają żywność",
                        value="Brak",
                        disabled=True,
                    ),
                    mui.LabelInput(
                        "Data Urodzenia",
                        title="Dla statystyk, oraz by określić średnią wieku na wydarzeniach",
                        type="date",
                        disabled=True,
                    ),
                    mui.Button("Zapisz", disabled=True),
                    mui.DividerSplit("Połączone konta"),
                    mui.Grid(
                        mui.Button("", PROVIDERS.get(k.title(), k.title()), " - ", v.get("full_name"), disabled=True)
                        for k, v in identities.items()
                    ),
                )
            )
        )

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
                    mui.DivCentered(mui.Legend("0/100"), mui.Progress(title="0/100", value=0)),
                    header=mui.DivFullySpaced(
                        self.display_name,
                        fh.Img(src=session.get("picture"), height="64", width="64"),
                    ),
                ),
                fh.A(mui.Button("Ustawienia"), href="/profile/settings"),
                mui.DivCentered(
                    mui.Card(
                        mui.DividerSplit("Przejdź do"),
                        mui.Grid(
                            mui.Button(fh.A("Wydarzeń", href="/events")),
                            mui.Button(fh.A("Feedbacku", href="/feedback"), disabled=True),
                            cols=2,
                        ),
                        mui.DividerSplit("Zarządzaj"),
                        mui.Grid(
                            mui.Button(fh.A("Zadania", href="/quests"), disabled=True),
                            mui.Button(fh.A("Poziomy", href="/profile/levels"), disabled=True),
                            mui.Button(fh.A("Postać", href="/characters"), disabled=True),
                            mui.Button(fh.A("Ekwipunek", href="/items"), disabled=True),
                            cols=4,
                        ),
                        mui.DividerSplit("Moje..."),
                        mui.Grid(
                            mui.Button(fh.A("Wydarzenia", href="/events/mine")),
                            mui.Button(fh.A("Deklaracje", href="/contributions"), disabled=True),
                            mui.Button(fh.A("Bilety", href="/tickets"), disabled=True),
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
