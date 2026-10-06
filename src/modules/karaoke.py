from fasthtml import common as fh
from src import components as mu
from monsterui import all as mui
from src.modules.profile import FormInput
from src.components.headers import HEADERS
from src.components.app_factory import make_app
from src.db import Base

app, rt = fh.fast_app(hdrs=HEADERS)
rt = make_app("karaoke")


class Songs(Base):
    id: int | None = None
    created_at: str | None = None
    title: str | None = None
    artist: str | None = None
    is_available: bool | None = None
    is_requested: bool | None = None
    requested_by: str | None = None
    url: str | None = None


@rt
def request(session, song: Songs):
    if not Songs.maybe_one(Songs.select(session["auth"]).eq("title", song.title).eq("artist", song.artist)):
        song.requested_by = session["id"]
        song.is_requested = False
        song.insert(session["auth"])
        return search(session, song)
    else:
        return "Już poproszono o dodanie tego utworu. Odśwież stronę."


@rt
def search(session, query: Songs):
    q = Songs.select(session["auth"])
    q = q.ilike("artist", f"%{query.artist}%")
    if query.title:
        q = q.text_search("title", query.title)
    res = Songs.get(q)
    if not res:
        return (
            mui.Alert(
                "Nic nie znaleziono :( Aby dodać nowy utwór, znajdź go na jednej z tych stron i wstaw w pole URL:"
            ),
            fh.Ul(
                fh.Li(mu.Link("https://ultrastar-es.org/en/canciones", "UltraStar-Es")),
                fh.Li(mu.Link("https://usdb.eu/", "USDB.eu")),
                fh.Li(mu.Link("https://usdb.animux.de/", "USDB.de")),
            ),
            fh.Form(
                mui.Grid(
                    mui.LabelInput("Artysta", id="artist", value=query.artist),
                    mui.LabelInput("Tytuł", id="title", value=query.title),
                    mui.LabelInput("URL", id="url", required=True),
                ),
                mui.Button("Poproś o Dodanie", cls=mu.ButtonT.active + "w-full"),
                hx_post="/karaoke/request",
                hx_swap="innerHTML",
                hx_target="#songs",
            ),
        )
    return mui.TableFromLists(
        ["Artysta", "Tytuł", "Dostępne?"],
        [(r.artist, r.title, "✅" if r.is_available is True else "❌") for r in res],
    )


@rt
@mu.with_layout(mu.Layout)
def songs(session):
    return (
        fh.Form(
            mui.Grid(mui.LabelInput("Artysta", id="artist"), mui.LabelInput("Tytuł", id="title")),
            mui.Button("Szukaj", cls=mu.ButtonT.secondary + "w-full"),
            hx_post="/karaoke/search",
            hx_target="#songs",
            hx_swap="innerHTML",
        ),
        fh.Div(id="songs"),
    )
