from monsterui import all as mui
from dataclasses import dataclass
from fasthtml import common as fh
from src.components.headers import HEADERS
from src.beforeware import beforeware
from src.db import s

app, rt = fh.fast_app(hdrs=HEADERS, before=[beforeware])


@dataclass
class Item:
    id: int = None
    event_id: int = None
    name: str = None
    description: str = None
    quantity: int = None
    contributions: list["Contribution"] = list

    @classmethod
    def form(cls):
        return mui.Card(
            mui.Form(
                mui.Grid(
                    mui.LabelInput("Name"),
                    mui.LabelInput("Quantity", value=0, type="number", inputmode="numeric"),
                ),
                mui.LabelInput("Description"),
                mui.Button("Submit"),
            )
        )

    def display(self):
        filled = sum(c.quantity for c in self.contributions)
        return mui.AccordionItem(
            f"{self.name} x {filled}/{self.quantity}",
            mui.Card(self.description) if self.description else None,
            *(c.display() for c in self.contributions) if self.contributions else "Jeszcze nikt się nie zgłosił!",
            Contribution.form(),
        )

    @classmethod
    def fetch(cls, event_id: int) -> list["Item"]:
        return [
            Item(**i)
            for i in s.table("Items")
            .select('*, contributions:"Contributions" (*)')
            .eq("event_id", event_id)
            .execute()
            .data
        ]

    def add(self):
        s.table("Items").upsert(
            {
                "id": self.id,
                "event_id": self.event_id,
                "name": self.name,
                "description": self.description,
                "quantity": self.quantity,
            }
        ).execute()


@dataclass
class Contribution:
    item_id: int = None
    user_id: int = None
    quantity: int = None
    note: str = None

    def display(self):
        return mui.Card(self.note, header=f"{self.user_id} x {self.quantity}")

    @classmethod
    def form(cls):
        return mui.Card(
            mui.Form(
                mui.Grid(
                    mui.LabelInput("Your Quantity", value=0, type="number", inputmode="numeric"),
                    mui.LabelInput("Note"),
                ),
                mui.Button("Submit"),
            )
        )

    @classmethod
    def fetch(cls, item_id: int) -> list["Contribution"]:
        return [Contribution(**i) for i in s.table("Contributions").select("*").eq("item_id", item_id).execute().data]

    def add(self):
        s.table("Contributions").upsert(
            {
                "item_id": self.item_id,
                "user_id": self.user_id,
                "quantity": self.quantity,
                "note": self.note,
            }
        ).execute()


@rt("/{event_id}")
def contributions(session, event_id: int):
    # items = Item.fetch(event_id)
    items = [
        Item(0, 20, "Test", "stuff", 1, []),
        Item(1, 20, "coś", "something", 10, [Contribution(1, "abc", 5)]),
        Item(2, 20, "a", None, 20, [Contribution(2, "eee", 3, "stuff"), Contribution(2, "ef", 3)]),
        Item(3, 20, "b", None, 5, []),
    ]
    return mui.DivCentered(mui.Accordion(*(item.display() for item in items), Item.form()))
