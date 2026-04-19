from monsterui import all as mui
from dataclasses import dataclass, field
from fasthtml import common as fh
from src.components.headers import HEADERS
from src.beforeware import beforeware
from src.db import s

app, rt = fh.fast_app(hdrs=HEADERS, before=[beforeware])


@dataclass
class Item:
    id: int = None
    event_id: int = None
    user_id: int = None
    name: str = None
    description: str = None
    quantity: int = None
    contributions: list["Contribution"] = field(default_factory=list)

    def __post_init__(self):
        if self.contributions:
            self.contributions = [
                Contribution(display_name=(c.pop("user") or {}).get("display_name", c.get("user_id")), **c)
                for c in self.contributions
            ]

    @classmethod
    def form(cls, event_id: int):
        return mui.Card(
            mui.Form(
                mui.Grid(
                    mui.LabelInput("Name"),
                    mui.LabelInput("Quantity", value=1, type="number", inputmode="numeric"),
                ),
                mui.LabelInput("Description"),
                mui.Button(
                    "Submit",
                    hx_post=f"/contributions/items/{event_id}",
                    hx_target="#items",
                    hx_swap="beforeend",
                ),
            )
        )

    def display(self):
        filled = sum(c.quantity for c in self.contributions) if self.contributions else 0
        user_contributed = next(filter(lambda x: x.user_id == self.user_id, self.contributions), Contribution())
        return mui.AccordionItem(
            f"{self.name} x {filled}/{self.quantity}",
            mui.Card(self.description) if self.description else None,
            fh.Div(
                *(c.display() for c in self.contributions) if self.contributions else "Jeszcze nikt się nie zgłosił!",
                id=f"contributions-{self.id}",
            ),
            Contribution.form(self.id, contribution=user_contributed),
        )

    @classmethod
    def fetch(cls, event_id: int) -> list["Item"]:
        return [
            Item(**i)
            for i in s.table("Items")
            .select('*, contributions:"Contributions" (*, user:"users" (display_name))')
            .eq("event_id", event_id)
            .eq("contributions.user.event_id", event_id)
            .execute()
            .data
        ]

    def add(self):
        item = {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "quantity": self.quantity,
        }
        if self.id:
            item["id"] = self.id
        return Item(**s.table("Items").upsert(item).execute().data[0])


@dataclass
class Contribution:
    item_id: int = None
    user_id: int = None
    quantity: int = 0
    note: str = None
    created_at: str = None
    display_name: str = None

    def display(self):
        return mui.Card(
            self.note,
            header=f"{self.display_name} x {self.quantity}",
            id=f"contributions-{self.item_id}-{self.user_id}",
        )

    @classmethod
    def form(cls, item_id: int, contribution: "Contribution"):
        return mui.Card(
            mui.Form(
                mui.Grid(
                    mui.LabelInput(
                        "Your Quantity", id="quantity", value=contribution.quantity, type="number", inputmode="numeric"
                    ),
                    mui.LabelInput("Note", value=contribution.note),
                ),
                mui.Button(
                    "Submit",
                    hx_post=f"/contributions/contribute/{item_id}",
                    hx_target=f"#contributions-{item_id}"
                    + (f"-{contribution.user_id}" if contribution.user_id else ""),
                    hx_swap="afterend" if not contribution.user_id else "innerHTML",
                ),
            )
        )

    @classmethod
    def fetch(cls, item_id: int) -> list["Contribution"]:
        return [Contribution(**i) for i in s.table("Contributions").select("*").eq("item_id", item_id).execute().data]

    def add(self):
        return Contribution(
            **s.table("Contributions")
            .upsert(
                {
                    "item_id": self.item_id,
                    "user_id": self.user_id,
                    "quantity": self.quantity,
                    "note": self.note,
                }
            )
            .execute()
            .data[0]
        )


@rt("/items/{event_id}")
def add(session, event_id: int, responses: dict):
    item = Item(event_id=event_id, user_id=session["id"], **responses)
    item = item.add()
    return item.display()


@rt("/contribute/{item_id}")
def contribute(session, item_id: int, responses: dict):
    c = Contribution(user_id=session["id"], item_id=item_id, **responses)
    c = c.add()
    c.display_name = session.get("display_name", "Ty")
    return c.display()


@rt("/{event_id}")
def contributions(event_id: int):
    items = Item.fetch(event_id)
    return mui.DivCentered(mui.Accordion(*(item.display() for item in items), Item.form(event_id), id="items"))
