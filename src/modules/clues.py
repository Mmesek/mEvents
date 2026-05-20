from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE, with_layout
from src.components.app_factory import make_app
from src.db import Base

rt = make_app("qr")


class Clue(Base):
    id: int | None = None
    name: str | None = None
    description: str | None = None
    url: str | None = None


class Clue_QR(Base):
    qr: str | None = None
    clue_id: int | None = None
    clue: Clue | None = None


class Clues_Collected(Base):
    user_id: int
    clue_id: int


@rt("/{qr}")
@with_layout(title="Znaleziona wskazówka")
def collect_clue(session, qr: str):
    try:
        clue = Clue_QR.get_one(Clue_QR.select(session["auth"], 'clue:"Clue" (*)').eq("qr", qr))
    except Exception as ex:
        return mui.Small("Nie znaleziono podanej wskazówki")
    clue = clue.clue
    Clues_Collected(session["id"], clue.id).upsert(session["auth"])

    return fh.Div(
        mui.Card(
            fh.Img(src=clue.url, loading="lazy", width=200, height=200) if clue.url else None,
            header=mui.H1(clue.name),
            footer=mui.DivCentered(mui.Small(clue.description)),
        )
    )
