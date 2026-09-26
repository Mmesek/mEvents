from fasthtml import common as fh
from monsterui.all import Button, ButtonT, DivCentered, DivRAligned, render_md
from src import components as mu
from monsterui import all as mui

from src.db import s
from src.components.headers import HEADERS
from src.components.app_factory import make_app
from src.db import Base
from src.components import TIMEZONE, Layout, back_to_main, handle_updating_responses, with_layout
from src.modules.profile import Profile, FormInput

app, rt = fh.fast_app(hdrs=HEADERS)
rt = make_app("character")


class Part:
    name: str
    description: str

    def render(self):
        return mui.Card(
            mui.render_md(self.description) if self.description else None,
            header=mui.DivCentered(self.name) if self.name else None,
        )


class Character_Secret(Part, Base):
    id: int
    name: str | None = None
    description: str | None = None
    max_usage: int | None = None
    requires: list[int] | None = None


class Character_Quest(Part, Base):
    id: int
    name: str | None = None
    description: str | None = None
    max_usage: int | None = None
    mutual_exclusive: list[int] | None = None
    requires: list[int] | None = None


class Character_Challenge(Part, Base):
    id: int
    name: str | None = None
    description: str | None = None
    max_usage: int | None = None
    mutual_exclusive: list[int] | None = None
    requires: list[int] | None = None


class Character_Background(Part, Base):
    id: int
    name: str | None = None
    description: str | None = None
    max_usage: int | None = None
    requires: list[int] | None = None


class Character_Cover(Part, Base):
    id: int
    name: str | None = None
    description: str | None = None
    max_usage: int | None = None


class Character_Challenges(Base):
    character_id: str
    challenge_id: int
    challenge: Character_Challenge


class Character(Base):
    id: str
    secret_id: int | None = None
    quest_id: int | None = None
    challenge_id: int | None = None
    background_id: int | None = None
    cover_id: int | None = None

    secret: Character_Secret | None = None
    quest: Character_Quest | None = None
    challenges: list[Character_Challenge] | None = None
    background: Character_Background | None = None
    cover: Character_Cover | None = None


@rt
def update_profile(answers: Profile, session):
    Profile.table(session["auth"]).update({"birthday": answers.birthday.isoformat()}).eq(
        "user_id", session["id"]
    ).execute()


from datetime import datetime

SIGNS = {
    "Aries": ((3, 21), (4, 19)),
    "Taurus": ((4, 20), (5, 20)),
    "Gemini": ((5, 21), (6, 20)),
    "Cancer": ((6, 21), (7, 22)),
    "Leo": ((7, 23), (8, 22)),
    "Virgo": ((8, 23), (9, 22)),
    "Libra": ((9, 23), (10, 22)),
    "Scorpio": ((10, 23), (11, 21)),
    "Sagittarius": ((11, 22), (11, 28)),
    "Ophiuchus": ((11, 29), (12, 17)),
    "Sagittarius_": ((12, 18), (12, 21)),
    "Capricorn": ((12, 22), (1, 19)),
    "Aquarius": ((1, 20), (2, 18)),
    "Pisces": ((2, 19), (3, 20)),
}


def sun_sign(dt: datetime) -> str:
    for sign, ranges in SIGNS.items():
        start, end = ranges
        start_month, start_day = start
        end_month, end_day = end
        if (start_month == dt.month and start_day <= dt.day) or (dt.month == end_month and dt.day <= end_day):
            return sign.replace("_", "")


NAMES = {
    "Aries": "Baran",
    "Taurus": "Byk",
    "Gemini": "Bliźnięta",
    "Cancer": "Rak",
    "Leo": "Lew",
    "Virgo": "Panna",
    "Libra": "Waga",
    "Scorpio": "Skorpion",
    "Sagittarius": "Strzelec",
    "Ophiuchus": "Wężownik",
    "Capricorn": "Koziororzec",
    "Aquarius": "Wodnik",
    "Pisces": "Ryby",
}

ELEMENTS = {
    "Aries": "Ogień",
    "Taurus": "Ziemia",
    "Gemini": "Powietrze",
    "Cancer": "Woda",
    "Leo": "Ogień",
    "Virgo": "Ziemia",
    "Libra": "Powietrze",
    "Scorpio": "Woda",
    "Sagittarius": "Ogień",
    "Ophiuchus": "Eter",
    "Capricorn": "Ziemia",
    "Aquarius": "Powietrze",
    "Pisces": "Woda",
}

MODALITIES = {
    "Aries": "Kardynalna",
    "Taurus": "Stała",
    "Gemini": "Zmienna",
    "Cancer": "Kardynalna",
    "Leo": "Stała",
    "Virgo": "Zmienna",
    "Libra": "Kardynalna",
    "Scorpio": "Stała",
    "Sagittarius": "Zmienna",
    "Ophiuchus": "Nieznana",
    "Capricorn": "Kardynalna",
    "Aquarius": "Stała",
    "Pisces": "Zmienna",
}


def get_zodiac(date: datetime):
    sign = sun_sign(date)
    return mui.Card(
        mui.DivCentered(
            mui.DivCentered(NAMES[sign], header="Znak Słoneczny"),
            mui.DivCentered(ELEMENTS[sign], header="Żywioł"),
            mui.DivCentered(MODALITIES[sign], header="Jakość"),
        )
    )


@rt("/")
@with_layout(Layout, "Postać")
def index(session, event_id: int = None):
    if not (_profile := Profile.maybe_one(Profile.select(session["auth"]).eq("user_id", session["id"]))):
        _profile = Profile(session["id"])
    if not _profile.birthday:
        session["referrer"] = "/character"
        return [
            mui.Form(
                FormInput(
                    "Data Urodzenia",
                    "Podaj swoją datę urodzenia aby wyświetlić postać",
                    value=_profile.birthday or None,
                    type="date",
                    id="birthday",
                ),
                mu.Button("Zapisz", cls=mu.ButtonT.primary + "w-full"),
                hx_post="/character/update_profile",
            )
        ]
    if not (
        character := Character.maybe_one(
            Character.select(
                session["auth"],
                '*, secret:secret_id (*), quest:quest_id (*), challenges:"Character_Challenge"!"Character_Challenges" (*), background:background_id (*), cover:cover_id (*)',
            ).eq("id", session["id"])
        )
    ):
        character = (
            s.auth(session["auth"])
            .rpc(
                "create_character_v2",
                {"user_id": session["id"], "challenge_count": 3},
            )
            .execute()
        )
        character = Character.maybe_one(
            Character.select(
                session["auth"],
                '*, secret:secret_id (*), quest:quest_id (*), challenges:"Character_Challenge"!"Character_Challenges" (*), background:background_id (*), cover:cover_id (*)',
            ).eq("id", session["id"])
        )
    return [
        mui.Accordion(
            mui.AccordionItem("Przykrywa", character.cover.render()) if character.cover else None,
            mui.AccordionItem("Sekret", character.secret.render()) if character.secret else None,
            mui.AccordionItem("Postać", character.background.render()) if character.background else None,
            mui.AccordionItem("Zadanie", character.quest.render()) if character.quest else None,
            mui.AccordionItem("Wyzwania", *[i.render() for i in character.challenges])
            if character.challenges
            else None,
            mui.AccordionItem("Zodiak", get_zodiac(_profile.birthday), open=True),
            multiple=True,
        )
    ]


@rt("/card")
def card(session, guest_id: str = None):
    if guest_id:
        session["guest_id"] = guest_id
    r = s.table("Cards").select("*").eq("user_id", session["guest_id"]).execute().data
    return DivCentered("Zadania", r[0]["tasks"]), DivCentered("Motywacja", r[0]["motivation"])
