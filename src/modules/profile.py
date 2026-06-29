from datetime import date
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
    user_id: str = None
    display_name: str = None
    email: str | None = None
    birthday: date | None = None
    place: str | None = None
    allergies: list[str] | None = None
    photo_consent: bool = False

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
@with_layout(title="Ustawienia")
def settings(session):
    return _settings(session)
    # p = Profile.get_one(Profile.select(session["auth"]))
    # return Profile(session["id"], session["display_name"]).edit(session)


def FormField(
    title: str, description: str, *args, outer_id: str = None, required: bool = False, note: str = None, **kwargs
):
    return mui.Card(
        mui.DivCentered(fh.Legend(title, cls="fieldset-legend" + " uk-form-label-required" if required else "")),
        fh.P(description, cls="label"),
        fh.Div(*args, id=outer_id),
        fh.Small(note) if note else None,
        **kwargs,
    )


def FormInput(
    title: str,
    description: str,
    value: str = None,
    placeholder: str = None,
    type: str = None,
    id: str = None,
    outer_id: str = None,
    required: bool = False,
    note: str = None,
    **kwargs,
):
    return FormField(
        title,
        description,
        mui.Input(
            value=value,
            placeholder=placeholder,
            type=type,
            id=id,
            required=required,
            **kwargs,
        ),
        required=required,
        outer_id=outer_id,
        note=note,
    )


def FormInputs(
    title: str,
    description: str,
    values: str = None,
    placeholder: str = None,
    type: str = None,
    id: str = None,
    outer_id: str = None,
    **kwargs,
):
    return FormField(
        title,
        description,
        *[mui.Input(value=value, placeholder=placeholder, type=type, id=id, **kwargs) for value in values],
        outer_id=outer_id,
    )


def FormSwitch(title: str, description: str, checked: bool = None, id: str = None):
    return FormField(
        None,
        None,
        mui.DivHStacked(mui.Switch(id=id, checked=checked), fh.P(title)),
        note=description,
    )


@rt
@with_layout(title="Dokończ rejestrację konta")
def register(session):
    return _settings(session)


def _settings(session):
    if not (_profile := Profile.maybe_one(Profile.select(session["auth"]).eq("user_id", session["id"]))):
        _profile = Profile(session["id"], session["display_name"], session["email"])
    return (
        fh.Form(
            mui.DivCentered(
                fh.Small("Jeśli nie masz odpowiedzi na dane pytanie, pozostaw pole puste (Chyba że jest wymagane)"),
                fh.Small("Formularz możesz edytować w dowolnym momencie korzystając z tej samej strony."),
            ),
            FormInput(
                "Twoja Nazwa",
                "Imię Nazwisko bądź ksywka - czyli jak inni mogą Ciebie rozpoznać.",
                value=_profile.display_name or session["display_name"],
                placeholder="Imię Nazwisko / Kswyka",
                id="display_name",
                required=True,
                note="Tylko pierwsze imię oraz dwie litery nazwiska są widoczne publiczne - reszta jest widoczna tylko dla organizatora.",
            ),
            FormInput(
                "Podłączony adres e-mail",
                "E-mail do kontaktu. Tam będą wysyłane informacje organizacyjne o wydarzeniu",
                value=_profile.email or session["email"],
                placeholder="email@domain.tld",
                id="email",
                required=True,
            ),
            FormInput(
                "Data Urodzenia",
                "Dla statystyk, oraz by określić średnią wieku na wydarzeniach",
                value=_profile.birthday or None,
                type="date",
                id="birthday",
            ),
            FormSwitch(
                "Czy zgadzasz się na umieszczenie twojego wizerunku z wydarzenia na mediach społecznościowych?",
                "Ujęcia prawdopodobnie będą grupowe, a w takich przypadkach nieuchwycenie części z twarzy bywa zaskakująco trudne.",
                checked=_profile.photo_consent,
                id="photo_consent",
            ),
            FormInput(
                "Miasto Zamieszkania",
                "Dla statystyk, skąd są uczestnicy (Oraz by dopasować wydarzenia)",
                value=_profile.birthday or None,
                id="place",
            ),
            FormInputs(
                "Jeśli posiadasz alergie/uczulenia o których powinniśmy wiedzieć, podaj je tutaj",
                "Na przykład orzechy albo cukier",
                id="allergies",
                values=_profile.allergies or [""],
                hx_post="/profile/add-answer?id=allergies",
                hx_swap="beforeend",
                hx_target="#allergies-container",
                outer_id="allergies-container",
            ),
            mu.Button("Zapisz", cls=mu.ButtonT.primary + "w-full"),
            hx_post="/profile/finish-register",
        ),
    )


@rt("/add-answer")
def add_answer(id: str):
    return mui.Input(id=id, hx_post=f"/profile/add-answer?id={id}", hx_target=f"#{id}-container", hx_swap="beforeend")


@rt("/finish-register")
def finish_register(answers: Profile, session):
    answers.user_id = session["id"]
    answers.allergies = [a for a in answers.allergies if a]
    if answers.birthday:
        answers.birthday = answers.birthday.isoformat()
    resp = answers.to_dict()
    resp["photo_consent"] = resp.get("photo_consent", False)
    Profile.table(session["auth"]).upsert(resp).execute()
    return fh.Redirect(session.pop("referrer", "/"))
