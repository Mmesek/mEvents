from fasthtml import common as fh
from monsterui.all import (
    AT,
    H1,
    Card,
    DivCentered,
    DivLAligned,
    UkIconLink,
    Theme,
)


from db import s
from generators import info_card

app, rt = fh.fast_app(hdrs=Theme.orange.headers())


@rt("/")
def events():
    forms = s.table("Form").select("*").execute().data

    socials = (
        ("github", "https://github.com/Mmesek/mEvents"),
        ("messages-square", "https://discord.com"),
    )

    return (
        fh.Title("Nadchodzące wydarzenia"),
        DivCentered(H1("Nadchodzące wydarzenia")),
        *[
            info_card(
                fh.A(f["title"], cls=AT.classic, href=f"/form/{f['id']}"),
                # **f.info,
            )
            for f in forms
            # if f.info
        ],
        Card(
            footer=DivCentered(
                DivLAligned(*[UkIconLink(icon, href=url) for icon, url in socials])
            ),
        ),
    )
