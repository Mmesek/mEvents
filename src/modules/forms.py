from fasthtml import common as fh
from monsterui.all import (
    Button,
    ButtonT,
    DivCentered,
    DivRAligned,
    render_md,
    Container,
    Form,
    LabelInput,
    Options,
    LabelTextArea,
    DividerLine,
)

from src.beforeware import beforeware
from src.components import FormLayout, handle_updating_responses
from src.db import s
from src.forms import Question
from src.generators import guests, QuestionType
from src.modules.events import Event
from src.components.headers import HEADERS


app, rt = fh.fast_app(
    hdrs=HEADERS,
    before=beforeware,
)


def back_to_main():
    return fh.A(Button("Wróć do listy wydarzeń", cls=ButtonT.ghost, submit=False), href="/")


@rt("/guests")
def list_guests(event_id: str):
    r = s.table("Response").select("user_id").eq("event_id", event_id).execute().data
    names = s.table("users").select("display_name").in_("id", [i["user_id"] for i in r]).execute().data
    return DivCentered(fh.Ul((fh.Li(i["display_name"]) for i in names)))


def form(user_id, event_id):
    f = (
        s.table("Event")
        .select(
            'form:form_id (*, questions:"Form_Questions" (order, required, question:"Question" (*, options:"Question_Options" (id, value), answer:"Response" (value))))'
        )
        .eq("id", event_id)
        .eq("form.questions.question.answer.event_id", event_id)
        .eq("form.questions.question.answer.user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not f:
        return DivCentered("Podany formularz nie istnieje", back_to_main())
    f = f.data.get("form", {})
    questions = sorted(
        [Question(order=q.get("order"), required=q.get("required"), **q.get("question")) for q in f.get("questions")],
        key=lambda x: x.order,
    )
    content = [
        DivRAligned(
            guests(event_id, target="guestlist"),
            id="guestlist",
        )
    ]
    content.extend([q.generate() for q in questions])
    content.append(Button("Zapisz", cls=ButtonT.primary))
    info = Event(title=f["title"], **f.get("info")).info_card() if f.get("info") else None

    return info, FormLayout(
        "",
        render_md(f["description"]) if f["description"] else None,
        *content,
        destination=f"/forms/submit/{event_id}",
    )


@rt("/new")
def new():
    return fh.Title("Dynamic Form Builder"), Container(
        fh.Div(
            Form(
                LabelInput("Tytuł Formularza", id="form-title"),
                LabelTextArea("Opis Formularza (wspiera Markdown)", id="form-description"),
                fh.Div(
                    add_question(),
                    id="questions-list",
                ),
                Button("Submit All Questions", cls=ButtonT.primary, submit=True, hx_post="/forms/add"),
            ),
            cls="space-y-4",
        ),
    )


@rt("/add-question")
def add_question():
    return (
        LabelInput("Pytanie", placeholder="Pytanie", id="question"),
        LabelTextArea("Opis", placeholder="Description", id="description"),
        "Typ odpowiedzi",
        fh.Select(
            Options(*QuestionType.keys()),
            id="type",
            hx_target="#questions-list",
            hx_post="/forms/add-question",
            hx_swap="beforeend",
        ),
        DividerLine(),
    )


@rt("/add")
def add_form(responses: dict):
    print(responses)
    return "Added"


@rt("/{event_id}")
def event_form(session, event_id: str):
    return (
        fh.Title("Rejestracja na wydarzenie"),
        DivRAligned(
            "Zalogowano jako:",
            fh.Img(src=session.get("picture"), height="24", width="24"),
            session.get("email"),
        ),
        form(session["id"], event_id),
    )


@rt("/submit/{event}")
def submit(session, event: str, responses: dict):
    responses = handle_updating_responses(responses)

    try:
        s.table("Response").upsert(
            [
                {
                    "user_id": session["id"],
                    "event_id": event,
                    "question_id": k,
                    "value": [v],
                }
                for k, v in responses.items()
                if v
            ]
        ).execute()
    except:
        return DivCentered("Coś poszło nie tak... odśwież stronę i wprowadź odpowiedzi ponownie.")

    return DivCentered(
        f"Dzięki za zapis! Sprawdź swojego e-maila {session['email']} i potwierdź obecność gdy otrzymasz zaproszenie!"
    ), DivRAligned(back_to_main())
