import yaml
from components import FormLayout, icon_text
from fasthtml.common import A, Mount, Redirect, Title, fast_app, serve
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


def profile_form(event):
    if event == "Domówka":
        event = "questions"
    else:
        event = "campfire"
    f = load_questions_from_yaml(f"web/events/{event}.yaml")

    content = [q.generate() for q in f.questions]
    content.append(Button("Submit", cls=ButtonT.primary))

    return info_card(f.title, **f.info) if f.info else None, FormLayout(
        "", render_md(f.description) if f.description else None, *content
    )


@rt("/form/{event}")
def index(event: str):
    return (
        Title("Rejestracja na wydarzenie"),
        profile_form(event),
    )


@rt("/events")
def events():
    forms = [
        load_questions_from_yaml(f"web/events/{f}")
        for f in ["campfire.yaml", "feedback.yaml", "questions.yaml"]
    ]
    for f in forms:
        if f.info:
            f.info["description"] = None
    socials = (
        ("github", "https://github.com/Mmesek/web-events"),
        ("messages-square", "https://discord.com"),
        ("linkedin", "https://www.linkedin.com/in/isaacflath/"),
    )

    return (
        Title("Nadchodzące wydarzenia"),
        DivCentered(H1("Nadchodzące wydarzenia")),
        *[
            info_card(
                A(f.title, cls=AT.classic, href=f"/form/{f.title.split(' ')[0]}"),
                **f.info,
            )
            for f in forms
            if f.info
        ],
        Card(
            footer=DivCentered(
                DivLAligned(*[UkIconLink(icon, href=url) for icon, url in socials])
            ),
        ),
    )


@rt("/")
def main(session):
    if not session.get("email"):
        return Redirect("/login")
    return events()


serve()
