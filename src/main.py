from fasthtml.common import fast_app, serve, P, Div, Option, Title
from monsterui.all import (
    Theme,
    Titled,
    Card,
    H1,
    H3,
    Subtitle,
    DivLAligned,
    UkIconLink,
    TextPresets,
    LabelInput,
    LabelSelect,
    LabelTextArea,
    FormLabel,
    Input,
    Button,
    ButtonT,
    Container,
    DividerLine,
    Form,
    LabelRadio,
    Radio,
    Grid,
    LabelRange,
    LabelSwitch,
    TextArea,
    render_md,
    Switch,
    Range,
    UkIcon,
)


# Choose a theme color (blue, green, red, etc)
hdrs = Theme.orange.headers()

# Create your app with the theme
app, rt = fast_app(hdrs=hdrs)


def FormSectionDiv(*c, cls="space-y-2", **kwargs):
    return Card(*c, cls=cls, **kwargs)


def QuestionText(c):
    return H3(c, cls=TextPresets.muted_sm)


def HelpText(c):
    return P(c, cls=TextPresets.muted_sm)


def FormLayout(title, subtitle, *content, cls="space-y-3 mt-4"):
    return Container(Div(H1(title), subtitle, DividerLine(), Form(*content, cls=cls)))


def icon_text(icon, text):
    return (
        DivLAligned(
            UkIcon(icon),
            render_md(text),
            cls="space-y-0 space-x-1",
        ),
    )


def right_icon_text(icon, text):
    return (
        DivLAligned(
            render_md(text),
            UkIcon(icon),
            cls="space-y-0 space-x-1",
        ),
    )


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
    return Card(
        H1(title),
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
        icon_text("palette", f"**Temat Przewodni**: {theme}") if theme else None,
        icon_text("shirt", f"**Dresscode**: {dresscode}") if dresscode else None,
        icon_text(
            "messages-square",
            text=f"**Discord**: [Link do wydarzenia]({discord_event})",
        ),
        render_md(description) if description else None,
        body_cls="space-y-0",
    )


def generate_input(
    question: str,
    question_id: int,
    description: str = None,
    placeholder: str = None,
    **kwargs,
):
    return (
        QuestionText(question),
        HelpText(description),
        Input(id=question_id, placeholder=placeholder),
    )


def generate_long_input(
    question: str, question_id: int, description=None, placeholder=None, **kwargs
):
    return (
        QuestionText(question),
        HelpText(description),
        TextArea(id=question_id, placeholder=placeholder),
    )


def generate_text(description: str, *args, **kwargs):
    return P(render_md(description))


from functools import partial


def generate_radio(question: str, question_id: int, options: list[str], **kwargs):
    radio = partial(RadioLabel, name=question_id)
    return (
        FormLabel(question),
        *map(
            radio,
            options,
        ),
    )


def generate_hour_picker(
    question: str, question_id: int, description: str = None, **kwargs
):
    return (
        QuestionText(question),
        HelpText(description),
        Input(type="time", id=question_id, **kwargs),
    )


def generate_switch(question: str, question_id: int, description: str = None, **kwargs):
    return (
        Switch(question, id=question_id, **kwargs),
        HelpText(description),
    )


def generate_scale(
    question: str,
    question_id: int,
    min: int,
    max: int,
    description: str = None,
    **kwargs,
):
    return (
        QuestionText(question),
        HelpText(description),
        Range(min=min, max=max, name=question_id, **kwargs),
    )


def generate_date_picker(question: str, question_id: int, **kwargs):
    return LabelInput(question, type="date", id=question_id, **kwargs)


QuestionType = {
    "ANSWER": generate_input,
    "INPUT": generate_input,
    "LONG_INPUT": generate_long_input,
    "CHOICE": generate_radio,
    "HOUR": generate_hour_picker,
    "DATE": generate_date_picker,
    "SCALE": generate_scale,
    "BOOL": generate_switch,
    "TEXT": generate_text,
}


def RadioLabel(label, name):
    return DivLAligned(Radio(name=name, checked=(label == "Yes")), FormLabel(label))


from dataclasses import dataclass


@dataclass
class Question:
    id: int = None
    question: str = None
    type: str = None
    kwargs: dict = None
    description: str = None

    def generate(self):
        return FormSectionDiv(
            self.type(
                question=self.question,
                question_id=self.id,
                description=self.description,
                **(self.kwargs or {}),
            )
        )


@dataclass
class Forms:
    title: str
    description: str
    questions: list[Question]
    info: dict


import yaml


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


def profile_form():
    f = load_questions_from_yaml("web/events/campfire.yaml")

    content = [q.generate() for q in f.questions]
    content.append(Button("Submit", cls=ButtonT.primary))

    return info_card(f.title, **f.info) if f.info else None, FormLayout(
        "", render_md(f.description) if f.description else None, *content
    )


@rt
def index():
    socials = (
        ("github", "https://github.com/AnswerDotAI/MonsterUI"),
        ("twitter", "https://twitter.com/isaac_flath/"),
        ("linkedin", "https://www.linkedin.com/in/isaacflath/"),
    )
    return (
        Title("Rejestracja na wydarzenie"),
        profile_form(),
        Card(
            footer=DivLAligned(*[UkIconLink(icon, href=url) for icon, url in socials]),
        ),
    )


serve()
