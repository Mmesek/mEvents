import time

from fasthtml import common as fh
from monsterui.all import (
    Button,
    ButtonT,
    Container,
    DivCentered,
    DividerLine,
    DivRAligned,
    Form,
    LabelInput,
    LabelTextArea,
    render_md,
)

from src.beforeware import beforeware
from src.components import FormLayout, handle_updating_responses
from src.components.headers import HEADERS
from src.db import s
from src.forms import Question
from src.generators import QuestionType, guests
from src.modules.events import Event

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
                Button(
                    "Dodaj nowe pytanie",
                    hx_target="#questions-list",
                    hx_post="/forms/add-question",
                    hx_swap="beforeend",
                ),
                Button("Submit All Questions", cls=ButtonT.primary, submit=True, hx_post="/forms/add"),
            ),
            cls="space-y-4",
        ),
    )


@rt("/add-question")
def add_question():
    idx = int(time.time() % 10000)
    return fh.Div(
        fh.Input(id="order", type="hidden", value=idx),
        LabelInput("Pytanie", placeholder="Pytanie", id="question"),
        LabelTextArea("Opis", placeholder="Description", id="description"),
        "Typ odpowiedzi",
        question_type({}, idx),
        DividerLine(),
        id=idx,
    )


@rt("/question-type")
def question_type(responses: dict, idx: int = 0):
    selected = responses.get(f"type-{idx}", "ANSWER")
    print(responses)
    print(selected)
    items = [
        fh.Select(
            *[fh.Option(k, id=k, title=k, selected=selected == k) for k in QuestionType],
            hx_target=f"#type-{idx}",
            hx_post=f"/forms/question-type?idx={idx}",
            hx_swap="innerHTML",
            id=f"type-{idx}",
            title="Wybierz rodzaj pytania",
        )
    ]
    if selected == "SCALE":
        items.append(
            fh.Grid(
                LabelInput("Minimum", type="number", inputmode="numeric", value=0, id="min"),
                LabelInput("Maximum", type="number", inputmode="numeric", value=10, pattern=r"\d*", id="max"),
            )
        )
    if selected == "CHOICE":
        items.append(add_option(idx, 0))
    return fh.Div(*items, id=f"type-{idx}")


@rt("/add-option")
def add_option(idx: int, order: int):
    return fh.Input(
        id=f"option-{idx}-{order}",
        hx_post=f"/forms/add-option?idx={idx}&order={order + 1}",
        placeholder=f"Option {idx}",
        hx_target=f"#option-{idx}-{order}",
        hx_swap="afterend",
    )


def get_next(responses: dict, key: str):
    if type(responses[key]) is list:
        return next(responses[key])
    return responses[key]


@rt("/add")
def add_form(session, responses: dict):
    questions = []
    for idx, q, desc in zip(responses["order"], responses["question"], responses["description"], strict=True):
        question = {
            "type": responses[f"type-{idx}"],
            "title": q,
            "description": desc,
        }
        if responses[f"type-{idx}"] == "SCALE":
            question["min_length"] = get_next(responses, "min")
            question["max_length"] = get_next(responses, "max")
        if responses[f"type-{idx}"] == "CHOICE":
            options = []
            for k, v in responses.items():
                if k.startswith(f"option-{idx}") and v:
                    options.append(v)
            question["options"] = options
        questions.append(question)
    print(questions)
    return i18n.t("forms.create.success", locale=session.get("locale"))


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
