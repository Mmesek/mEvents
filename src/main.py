import yaml
from components import FormLayout, icon_text
from fasthtml.common import (
    A,
    Mount,
    Redirect,
    RedirectResponse,
    Title,
    fast_app,
    serve,
    Beforeware,
)
from fasthtml import common as fh
from forms import Forms, Question
from generators import QuestionType
from login import app as login_app
from monsterui.all import (
    AT,
    H1,
    Button,
    ButtonT,
    Card,
    DivCentered,
    DivLAligned,
    DivRAligned,
    Grid,
    Theme,
    UkIconLink,
    render_md,
)

# Choose a theme color (blue, green, red, etc)
hdrs = Theme.orange.headers()

# Create your app with the theme
app, rt = fast_app(hdrs=hdrs, routes=[Mount("/login", login_app)])


def info_card(
    title=None,
    start=None,
    end=None,
    date=None,
    place=None,
    theme=None,
    dresscode=None,
    dresscode_mandatory=None,
    discord_event=None,
    description=None,
):
    if dresscode and not dresscode_mandatory:
        dresscode += " *(Opcjonalnie)*"
    return DivCentered(
        Card(
            DivCentered(H1(title)),
            Grid(
                icon_text("clock", f"**Start**: {start}"),
                icon_text("clock", f"**Koniec**: {end}"),
                cols=2,
                cls="gap-1",
            ),
            Grid(
                icon_text("calendar", f"**Data**: {date}"),
                icon_text("pin", f"**Miejsce**: {place}"),
                cols=2,
                cls="gap-1",
            ),
            (icon_text("palette", f"**Temat Przewodni**: {theme}")) if theme else None,
            (icon_text("shirt", f"**Dresscode**: {dresscode}")) if dresscode else None,
            DivCentered(
                icon_text(
                    "messages-square",
                    text=f"**Discord**: [Link do wydarzenia]({discord_event})",
                )
            ),
            render_md(description) if description else None,
            body_cls="space-y-0",
        )
    )


def load_questions_from_yaml(file_path: str) -> Forms:
    """Loads questions from a YAML file into a list of Question dataclasses."""
    with open(file_path, "r") as f:
        questions_data = yaml.safe_load(f)
    return Forms(
        questions_data.get("title"),
        questions_data.get("description"),
        [
            Question(
                id=q.get("id"),
                question=q.get("question", q.get("description")),
                type=QuestionType.get(q.get("type")),
                description=q.get("description"),
                kwargs=q.get("kwargs"),
            )
            for q in questions_data.get("questions", [])
        ],
        questions_data.get("info"),
    )


import supabase, os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

s = supabase.create_client(SUPABASE_URL, SUPABASE_KEY).schema("forms")


def profile_form(event):
    f = (
        s.table("Form")
        .select('*, "Question" (*, "Question_Options" (*))')
        .eq("id", event)
        .single()
        .execute()
        .data
    )
    questions = [Question(**q) for q in f.get("Question")]

    content = [q.generate() for q in questions]
    content.append(Button("Submit", cls=ButtonT.primary))

    return info_card(f["title"], **f.get("info")) if f.get(
        "info"
    ) else None, FormLayout(
        "", render_md(f["description"]) if f["description"] else None, *content
    )


@rt("/form/{event}")
def index(session, event: str):
    return (
        Title("Rejestracja na wydarzenie"),
        DivRAligned(
            "Zalogowano jako:",
            fh.Img(src=session.get("picture"), height="24", width="24"),
            session.get("email"),
        ),
        profile_form(event),
    )


def require_login(func):
    def wrapped(session, *args, **kwargs):
        if not session.get("email"):
            return Redirect("/login")
        return func(session, *args, **kwargs)

    return wrapped


@rt("/events")
def events():
    forms = s.table("Form").select('*, "Question" (*)').execute().data

    socials = (
        ("github", "https://github.com/Mmesek/mEvents"),
        ("messages-square", "https://discord.com"),
    )

    return (
        Title("Nadchodzące wydarzenia"),
        DivCentered(H1("Nadchodzące wydarzenia")),
        *[
            info_card(
                A(f["title"], cls=AT.classic, href=f"/form/{f['id']}"),
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


@rt("/")
def main(session):
    return events()


serve()
