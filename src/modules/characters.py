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
from src.modules.zodiac import get_zodiac

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
def get_character(session, event_id: int):
    return Character.maybe_one(
        Character.select(
            session["auth"],
            '*, secret:secret_id (*), quest:quest_id (*), challenges:"Character_Challenge"!"Character_Challenges" (*), background:background_id (*), cover:cover_id (*)',
        ).eq("id", session["id"])
        # .eq("event_id", event_id)
    )


def ensure_birthday_set(session, _profile: Profile, referrer: str):
    session["referrer"] = referrer
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


@rt("/")
@with_layout(Layout, "Postać")
def index(session, event_id: int = None):
    if not (_profile := Profile.maybe_one(Profile.select(session["auth"]).eq("user_id", session["id"]))):
        _profile = Profile(session["id"])
    if not _profile.birthday:
        ensure_birthday_set("/character")
    if not (character := get_character(session, event_id)):
        character = (
            s.auth(session["auth"])
            .rpc(
                "create_character_v2",
                {"user_id": session["id"], "challenge_count": 3, "event_id": event_id},
            )
            .execute()
        )
        character = get_character(session, event_id)
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
