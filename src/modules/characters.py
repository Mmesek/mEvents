from fasthtml import common as fh
from monsterui.all import Button, ButtonT, DivCentered, DivRAligned, render_md
from src import components as mu
from monsterui import all as mui

from src.db import s
from src.components.headers import HEADERS
from src.components.app_factory import make_app
from src.db import Base
from src.components import TIMEZONE, Layout, back_to_main, handle_updating_responses, with_layout


app, rt = fh.fast_app(hdrs=HEADERS)
rt = make_app("character")


class Part:
    name: str
    description: str

    def render(self):
        return mui.Card(mui.render_md(self.description), header=mui.DivCentered(self.name))


class Character_Secret(Part, Base):
    id: int
    name: str
    description: str
    max_usage: int
    requires: list[int] | None = None


class Character_Quest(Part, Base):
    id: int
    name: str
    description: str
    max_usage: int
    mutual_exclusive: list[int] | None = None
    requires: list[int] | None = None


class Character_Challenge(Part, Base):
    id: int
    name: str
    description: str
    max_usage: int
    mutual_exclusive: list[int] | None = None
    requires: list[int] | None = None


class Character_Background(Part, Base):
    id: int
    name: str
    description: str
    max_usage: int
    requires: list[int] | None = None


class Character_Cover(Part, Base):
    id: int
    name: str
    description: str
    max_usage: int


class Character(Base):
    id: str
    secret_id: int | None = None
    quest_id: int | None = None
    challenge_id: int | None = None
    background_id: int | None = None
    cover_id: int | None = None

    secret: Character_Secret | None = None
    quest: Character_Quest | None = None
    challenge: Character_Challenge | None = None
    background: Character_Background | None = None
    cover: Character_Cover | None = None


@rt("/")
@with_layout(Layout, "Postać")
def index(session, event_id: int = None):
    if not (
        character := Character.maybe_one(
            Character.select(
                session["auth"],
                "*, secret:secret_id (*), quest:quest_id (*), challenge:challenge_id (*), background:background_id (*), cover:cover_id (*)",
            ).eq("id", session["id"])
        )
    ):
        character = (
            s.auth(session["auth"])
            .rpc(
                "create_character",
                {"user_id": session["id"]},
            )
            .execute()
        )
        character = Character.maybe_one(
            Character.select(
                session["auth"],
                "*, secret:secret_id (*), quest:quest_id (*), challenge:challenge_id (*), background:background_id (*), cover:cover_id (*)",
            ).eq("id", session["id"])
        )
    return [
        mui.Accordion(
            mui.AccordionItem("Przykrywa", character.cover.render()) if character.cover else None,
            mui.AccordionItem("Sekret", character.secret.render()) if character.secret else None,
            mui.AccordionItem("Postać", character.background.render()) if character.background else None,
            mui.AccordionItem("Zadanie", character.quest.render()) if character.quest else None,
            mui.AccordionItem("Wyzwanie", character.challenge.render()) if character.challenge else None,
            multiple=True,
        )
    ]


@rt("/card")
def card(session, guest_id: str = None):
    if guest_id:
        session["guest_id"] = guest_id
    r = s.table("Cards").select("*").eq("user_id", session["guest_id"]).execute().data
    return DivCentered("Zadania", r[0]["tasks"]), DivCentered("Motywacja", r[0]["motivation"])
