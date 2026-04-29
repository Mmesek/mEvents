from datetime import datetime
from typing import Annotated
from uuid import UUID

from fasthtml import common as fh
from monsterui import all as mui
from msgspec import Meta, field

from src.components import TIMEZONE, with_layout
from src.components.app_factory import make_app
from src.db import Base

rt = make_app("contributions")

uint = Annotated[int, Meta(ge=0)]


class Items(Base):
    id: int = None
    event_id: int = None
    user_id: UUID = None
    name: str = None
    description: str = None
    quantity: uint = None
    created_at: datetime = None
    contributions: list["Contributions"] = field(default_factory=list)

    def __post_init__(self):
        self.quantity = int(self.quantity)

    @classmethod
    def form(cls, event_id: int) -> fh.FT:
        return mui.Card(
            mui.Form(
                mui.Grid(
                    mui.LabelInput("Nazwa", id="name"),
                    mui.LabelInput("Ilość", id="quantity", value=1, type="number", inputmode="numeric", min=0),
                ),
                mui.LabelInput(
                    "Opis",
                    id="description",
                    placeholder="Dlaczego ten przedmiot jest potrzebny bądź jak interpretować ilość?",
                ),
                mui.Button(
                    "Dodaj",
                    hx_post=f"/contributions/items/{event_id}",
                    hx_target="#items",
                    hx_swap="beforeend",
                    cls=mui.ButtonT.ghost,
                ),
            ),
            header="Dodaj własną sugestię. W celu deklaracji przyniesienia sugerowanego przedmiotu, odśwież stronę i zadeklaruj odpowiedni przedmiot.",
        )

    def display(self, user_id: UUID = None):
        if user_id:
            user_id = UUID(user_id)
        filled = sum(c.quantity for c in self.contributions) if self.contributions else 0
        user_contributed = next(filter(lambda x: x.user_id == user_id, self.contributions), Contributions())
        return mui.AccordionItem(
            f"{self.name} x {filled}/{self.quantity}",
            mui.Card(self.description) if self.description else None,
            fh.Div(
                *(c.display() for c in sorted(self.contributions, key=lambda x: x.quantity, reverse=True))
                if self.contributions
                else "Jeszcze nikt się nie zgłosił!",
                id=f"contributions-{self.id}",
            ),
            Contributions.form(self.id, contribution=user_contributed),
        )

    @classmethod
    def fetch(cls, auth: str, event_id: int) -> list["Items"]:
        return Items.get(
            Items.table(auth)
            .select('*, contributions:"Contributions" (*, user:"users" (display_name))')
            .eq("event_id", event_id)
            .eq("contributions.user.event_id", event_id)
        )

    def add(self, auth: str):
        item = {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "quantity": max(self.quantity, 0),
        }
        if self.id:
            item["id"] = self.id
        return Items.get_one(Items.table(auth).upsert(item))


class Contributions(Base):
    item_id: int = None
    user_id: UUID = None
    quantity: uint = 0
    note: str = None
    created_at: datetime = None
    updated_at: datetime = None
    display_name: str = None
    user: dict = None

    def __post_init__(self):
        self.display_name = (self.user or {}).get("display_name", self.user_id)
        self.quantity = int(self.quantity)

    def display(self):
        return mui.Card(
            self.note,
            header=f"{self.display_name} x {self.quantity}",
            id=f"contributions-{self.item_id}-{self.user_id}",
        )

    @classmethod
    def form(cls, item_id: int, contribution: "Contributions") -> fh.FT:
        return mui.Card(
            mui.Form(
                mui.Grid(
                    mui.LabelInput(
                        "Twoja deklarowana ilość",
                        id="quantity",
                        value=contribution.quantity or 1,
                        type="number",
                        inputmode="numeric",
                        min=0,
                    ),
                    mui.LabelInput("Notatka", id="note", value=contribution.note),
                ),
                mui.Button(
                    "Zadeklaruj",
                    hx_post=f"/contributions/contribute/{item_id}",
                    hx_target=f"#contributions-{item_id}"
                    + (f"-{contribution.user_id}" if contribution.user_id else ""),
                    hx_swap="afterend" if not contribution.user_id else "innerHTML",
                    cls=mui.ButtonT.ghost,
                ),
            )
        )

    @classmethod
    def fetch(cls, auth: str, item_id: int) -> list["Contributions"]:
        return Contributions.get(Contributions.select(auth).eq("item_id", item_id))

    def add(self, auth: str):
        return Contributions.get_one(
            Contributions.table(auth).upsert(
                {
                    "item_id": self.item_id,
                    "user_id": self.user_id,
                    "quantity": max(self.quantity, 0),
                    "note": self.note,
                    "updated_at": datetime.now(TIMEZONE).isoformat(),
                }
            )
        )


@rt("/items/{event_id}")
def add(session, event_id: int, responses: dict):
    item = Items(event_id=event_id, user_id=session["id"], **responses)
    item = item.add(session["auth"])
    return item.display(session["id"])


@rt("/contribute/{item_id}")
def contribute(session, item_id: int, responses: dict):
    c = Contributions(user_id=session["id"], item_id=item_id, **responses)
    c = c.add(session["auth"])
    c.display_name = session.get("display_name", "Ty")
    return c.display()


@rt("/{event_id}")
@with_layout(title="Lista przedmiotów potrzebnych do wydarzenia")
def contributions(session, event_id: int):
    items = Items.fetch(session["auth"], event_id)
    return mui.Card(
        mui.Accordion(
            *(item.display(session["id"]) for item in sorted(items, key=lambda x: x.quantity, reverse=True)),
            Items.form(event_id),
            id="items",
        ),
    )
