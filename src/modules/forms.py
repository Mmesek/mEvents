from datetime import datetime

from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE, FormLayout, Layout, handle_updating_responses, with_layout
from src.components.app_factory import make_app
from src.components.models import Form, Response, Question as Question_db
from src.forms import Question
from src.generators import QuestionType
from src.modules.events import Event
from src.modules.tickets import Attendance
from src.db import s

rt = make_app("forms")


def back_to_main():
    return fh.A(mui.Button("Wróć do listy wydarzeń", cls=mui.ButtonT.ghost, submit=False), href="/")


def form(f, event_id, path="submit"):
    if not f:
        return mui.DivCentered("Podany formularz nie istnieje", back_to_main())
    f = f.data.get("form") or {}
    questions = sorted(
        [
            Question(order=q.get("order"), required=q.get("required"), **q.get("question", {}))
            for q in f.get("questions", [])
        ],
        key=lambda x: x.order,
    )
    content = [q.generate(event_id) for q in questions]
    if not questions:
        content.append(back_to_main())
    else:
        content.append(mui.Button("Zapisz", cls=mui.ButtonT.primary))
    info = Event(title=f["title"], **f.get("info")).info_card() if f.get("info") else None

    return info, FormLayout(
        "",
        mui.render_md(f.get("description")) if f.get("description") else None,
        *content,
        destination=f"/forms/{path}/{event_id}",
    )


@rt("/save/{event_id}")
def save(session, responses: dict, event_id: int):
    responses = handle_updating_responses(responses)
    Response.table(session["auth"]).upsert(
        [
            {
                "user_id": session["id"],
                "event_id": event_id,
                "question_id": k,
                "value": [v],
            }
            for k, v in responses.items()
            if v
        ]
    ).execute()


@rt
def new(session, t, form_id: int = None):
    res = Form()
    if form_id:
        res = Form.get_one(
            Form.select(
                session["auth"],
                '*, questions:"Form_Questions" (order, required, ..."Question" (*, options:"Question_Options" (id, value)))',
            ).eq("id", form_id)
        )

    return FormLayout(
        t("forms.create.title"),
        t("forms.create.help"),
        mui.Input(placeholder=t("forms.create.name"), id="form-title", required=True, cls="required", value=res.title),
        mui.TextArea(res.description, placeholder=t("forms.create.description"), id="form-description"),
        mui.DividerLine(),
        fh.Div(
            *[
                q.edit_form(session)
                for q in sorted(
                    [Question(**q) for q in res.questions or [{"id": 0}]],
                    key=lambda x: x.order,
                )
            ],
            id="questions-list",
        ),
        fh.Grid(
            mui.Button(
                t("forms.create.add_question"),
                hx_target="#questions-list",
                hx_post="/forms/add-question",
                hx_swap="beforeend",
            ),
            fh.Div(
                fh.Label(t("events.create.select_form")),
                fh.Select(
                    *[
                        fh.Option(
                            f["title"],
                            hx_post=f"/forms/add-question?question_id={f['id']}",
                        )
                        for f in Question_db.select(session["auth"], "id, title").execute().data
                    ],
                    searchable=True,
                    hx_target="#questions-list",
                    hx_swap="beforeend",
                ),
            ),
        ),
        mui.Button(t("forms.create.submit"), cls=mui.ButtonT.primary),
        cls="space-y-4",
        destination="/forms/add",
    )


@rt("/add-question")
def add_question(session, responses: dict, question_id: int = None):
    if type(responses["order"]) is not list:
        responses["order"] = [responses["order"]]
    order = len(responses["order"])
    if question_id:
        res = (
            Question_db.get_one(
                Question_db.select(
                    session["auth"],
                    '*, options:"Question_Options" (*)',
                ).eq("id", question_id)
            )
            or Question_db()
        )
        return Question(
            res.id,
            res.title,
            res.type,
            max_length=res.max_length,
            min_length=res.min_length,
            options=res.options,
            allow_multiple_answer=res.allow_multiple_answers,
        ).edit_form(session, order + 1)
    return Question().edit_form(session, order + 1)


@rt("/question-type")
def question_type(session, t, responses: dict, idx: int = 0, __selected: str = None):
    selected = __selected or responses.get(f"select-type-{idx}", "ANSWER")
    items = [
        fh.Select(
            *[fh.Option(k, id=k, title=k, selected=selected == k) for k in QuestionType],
            hx_target=f"#type-{idx}",
            hx_post=f"/forms/question-type?idx={idx}",
            hx_swap="outerHTML",
            id=f"select-type-{idx}",
            title=t("forms.create.type"),
        )
    ]
    if selected == "SCALE":
        items.append(
            fh.Grid(
                mui.Input(title="Minimum", type="number", inputmode="numeric", value=0, id="min"),
                mui.Input(title="Maximum", type="number", inputmode="numeric", value=10, pattern=r"\d*", id="max"),
            )
        )
    if selected == "CHOICE":
        items.append(add_option(session, idx, 0))
    return mui.DivCentered(*items, id=f"type-{idx}")


@rt("/add-option")
def add_option(t, idx: int, order: int):
    return mui.Input(
        id=f"option-{idx}-{order}",
        hx_post=f"/forms/add-option?idx={idx}&order={order + 1}",
        placeholder=t("forms.create.option", x=idx),
        hx_target=f"#option-{idx}-{order}",
        hx_swap="afterend",
    )


def get_next(responses: dict, key: str):
    if type(responses[key]) is list:
        return next(responses[key])
    return responses[key]


@rt
def add(session, t, responses: dict):
    questions = []
    if type(responses["order"]) is not list:
        responses["order"] = [responses["order"]]
        responses["question"] = [responses["question"]]
        responses["description"] = [responses["description"]]
    for idx, q, desc in zip(responses["order"], responses["question"], responses["description"], strict=True):
        if f"select-type-{idx}" not in responses:
            responses[f"select-type-{idx}"] = "INPUT"
        question = {
            "type": responses[f"select-type-{idx}"],
            "title": q,
            "description": desc,
        }
        if responses[f"select-type-{idx}"] == "SCALE":
            question["min_length"] = int(get_next(responses, "min"))
            question["max_length"] = int(get_next(responses, "max"))
        if responses[f"select-type-{idx}"] == "CHOICE":
            options = []
            for k, v in responses.items():
                if k.startswith(f"option-{idx}") and v:
                    options.append(v)
            question["options"] = options
        questions.append(question)
    res = (
        s.auth(session["auth"])
        .rpc(
            "create_form_with_questions",
            {"title": responses["form-title"], "description": responses["form-description"], "questions": questions},
        )
        .execute()
    )

    return t("forms.create.success")


@rt("/{event_id}")
@with_layout(Layout, "Rejestracja na wydarzenie")
def event_form(session, event_id: str):
    f = (
        Event.select(
            session["auth"],
            'form:form_id (*, questions:"Form_Questions" (order, required, question:"Question" (*, options:"Question_Options" (id, value), answer:"Response" (value))))',
        )
        .eq("id", event_id)
        .eq("form.questions.question.answer.event_id", event_id)
        .eq("form.questions.question.answer.user_id", session["id"])
        .maybe_single()
        .execute()
    )

    return form(f, event_id)


@rt("/feedback/{event_id}")
@with_layout(Layout, "Feedback z wydarzenia")
def feedback_form(session, event_id: str):
    f = (
        Event.select(
            session["auth"],
            'end_time, form:feedback_form_id (*, questions:"Form_Questions" (order, required, question:"Question" (*, options:"Question_Options" (id, value), answer:"Response" (value))))',
        )
        .eq("id", event_id)
        .eq("form.questions.question.answer.event_id", event_id)
        .eq("form.questions.question.answer.user_id", session["id"])
        .maybe_single()
        .execute()
    )
    if f and datetime.fromisoformat(f.data["end_time"]).astimezone(TIMEZONE) > datetime.now(TIMEZONE):
        return "Wróć po skończeniu wydarzenia!"

    return form(f, event_id, path="submit-feedback")


def save_to_db(session, event, responses):
    responses = handle_updating_responses(responses)

    Response.table(session["auth"]).upsert(
        [
            {
                "user_id": session["id"],
                "event_id": event,
                "question_id": k,
                "value": [v],
                "updated_at": datetime.now(TIMEZONE).isoformat(),
            }
            for k, v in responses.items()
            if v
        ]
    ).execute()
    Attendance.table(session["auth"]).upsert(
        {
            "event_id": event,
            "user_id": session["id"],
            "filled_form": datetime.now(TIMEZONE).isoformat(),
        }
    ).execute()


@rt("/submit/{event}")
def submit(session, event: str, responses: dict):
    try:
        save_to_db(session, event, responses)
    except Exception as ex:
        return mui.DivCentered("Coś poszło nie tak... odśwież stronę i wprowadź odpowiedzi ponownie.")
    return mui.DivCentered(
        "Dzięki za zapis!",
        mui.Button(
            fh.A("Pobierz bilet na wydarzenie", href=f"/tickets/qr?event_id={event}"),
            submit=False,
            cls=mui.ButtonT.primary,
        ),
        "Do wydarzeń plenerowych oraz imprez otrzymasz dodatkowo e-mail organizacyjny parę dni przed wydarzeniem - Sprawdź wtedy swoją skrzynkę odbiorczą:",
        mui.Button(session["email"], cls=mui.ButtonT.secondary, submit=False),
        "i potwierdź obecność gdy otrzymasz zaproszenie!",
    ), mui.DivRAligned(back_to_main())


@rt("/submit-feedback/{event}")
def submit_feedback(session, event: str, responses: dict):
    try:
        save_to_db(session, event, responses)
    except:
        return mui.DivCentered("Coś poszło nie tak... odśwież stronę i wprowadź odpowiedzi ponownie.")
    return mui.DivCentered("Dzięki za feedback! Zapraszam na następne wydarzenia!"), mui.DivRAligned(back_to_main())
