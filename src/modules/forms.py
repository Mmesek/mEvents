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
    Input,
    TextArea,
    render_md,
    Switch,
    ListT,
)
import i18n

from src.beforeware import beforeware
from src.components import FormLayout, handle_updating_responses, with_layout, Layout
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
    names = s.table("users").select("display_name").eq("event_id", event_id).order("timestamp").execute().data
    return DivCentered(fh.Ol(*[fh.Li(i["display_name"]) for i in names], cls=ListT.decimal))


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
def new(session, form_id: int = None):
    res = {}
    if form_id:
        res = (
            s.table("Form")
            .select(
                '*, questions:"Form_Questions" (order, required, ..."Question" (*, options:"Question_Options" (id, value)))'
            )
            .eq("id", form_id)
            .maybe_single()
            .execute()
            .data
            or {}
        )
    return fh.Title(i18n.t("forms.create.title", locale=session.get("locale"))), FormLayout(
        Input(
            placeholder=i18n.t("forms.create.name", locale=session.get("locale")),
            id="form-title",
            required=True,
            cls="required",
            value=res.get("title"),
        ),
        i18n.t("forms.create.help", locale=session.get("locale")),
        TextArea(
            res.get("description"),
            placeholder=i18n.t("forms.create.description", locale=session.get("locale")),
            id="form-description",
        ),
        DividerLine(),
        fh.Div(
            *[
                add_question(
                    session, q.get("title"), q.get("description"), q.get("order"), q.get("required"), q.get("type")
                )
                for q in res.get("questions", [{}])
            ],
            id="questions-list",
        ),
        fh.Grid(
            Button(
                i18n.t("forms.create.add_question", locale=session.get("locale")),
                hx_target="#questions-list",
                hx_post="/forms/add-question",
                hx_swap="beforeend",
            ),
            Button(
                i18n.t("forms.create.submit", locale=session.get("locale")),
                cls=ButtonT.primary,
            ),
        ),
        cls="space-y-4",
        destination="/forms/add",
    )


@rt("/add-question")
def add_question(
    session,
    __value: str = None,
    __description_value: str = None,
    __order: int = None,
    __required: bool = None,
    __type: str = None,
):
    idx = __order or int(time.time() % 10000)
    return fh.Div(
        fh.Input(id="order", type="hidden", value=idx),
        Input(
            placeholder=i18n.t("forms.create.question", locale=session.get("locale")),
            id="question",
            required=True,
            cls="required",
            value=__value,
        ),
        TextArea(
            __description_value,
            placeholder=i18n.t("forms.create.question_description", locale=session.get("locale")),
            id="description",
        ),
        Switch(i18n.t("forms.create.is_required", locale=session.get("locale")), id="is_required", checked=__required),
        question_type(session, {}, idx, __type),
        DividerLine(),
        id=idx,
    )


@rt("/question-type")
def question_type(session, responses: dict, idx: int = 0, __selected: str = None):
    selected = __selected or responses.get(f"select-type-{idx}", "ANSWER")
    items = [
        fh.Select(
            *[fh.Option(k, id=k, title=k, selected=selected == k) for k in QuestionType],
            hx_target=f"#type-{idx}",
            hx_post=f"/forms/question-type?idx={idx}",
            hx_swap="outerHTML",
            id=f"select-type-{idx}",
            title=i18n.t("forms.create.type", locale=session.get("locale")),
        )
    ]
    if selected == "SCALE":
        items.append(
            fh.Grid(
                Input(title="Minimum", type="number", inputmode="numeric", value=0, id="min"),
                Input(title="Maximum", type="number", inputmode="numeric", value=10, pattern=r"\d*", id="max"),
            )
        )
    if selected == "CHOICE":
        items.append(add_option(session, idx, 0))
    return DivCentered(*items, id=f"type-{idx}")


@rt("/add-option")
def add_option(session, idx: int, order: int):
    return Input(
        id=f"option-{idx}-{order}",
        hx_post=f"/forms/add-option?idx={idx}&order={order + 1}",
        placeholder=i18n.t("forms.create.option", locale=session.get("locale"), x=idx),
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
@with_layout(Layout, "Rejestracja na wydarzenie")
def event_form(session, event_id: str):
    return form(session["id"], event_id)


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
