from datetime import datetime

from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE, FormLayout, Layout, handle_updating_responses, with_layout, back_to_main
from src.components.app_factory import make_app
from src.components.models import Form, Response, Question, Question_Options

from src.generators import QuestionType
from src.modules.events import Event
from src.modules.tickets import Attendance
from src.db import s

mui.franken_class_map["ul"] = "list-[square] list-inside space-y-2 mb-6 ml-6 text-lg"


rt = make_app("forms")


def form(e: Event, path="submit"):
    return e.form.render(e.id, path)


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
                '*, questions:"Form_Questions" (order, required, question:"Question" (*, options:"Question_Options" (id, value)))',
            ).eq("id", form_id)
        )

    return FormLayout(
        t("forms.create.title"),
        t("forms.create.help"),
        mui.Input(
            placeholder=t("forms.create.name"),
            id="form-title",
            required=True,
            cls="required",
            disabled=bool(form_id),
            value=res.title,
        ),
        mui.TextArea(
            res.description, placeholder=t("forms.create.description"), id="form-description", disabled=bool(form_id)
        ),
        mui.DividerLine(),
        fh.Div(
            *[
                q.question.edit_form(session, q.order, q.required)
                for q in sorted(
                    res.questions or [],
                    key=lambda x: x.order,
                )
            ],
            id="questions-list",
        ),
        mui.Grid(
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
                        for f in Question.select(session["auth"], "id, title").execute().data
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
    order = responses.get("order", [])
    if type(order) is not list:
        responses["order"] = [responses["order"]]
    order = len(order)
    if question_id:
        res = (
            Question.get_one(
                Question.select(
                    session["auth"],
                    '*, options:"Question_Options" (*)',
                ).eq("id", question_id)
            )
            or Question()
        )
        return res.edit_form(session, order + 1)
    return Question().edit_form(session, order + 1)


@rt("/question-type")
def question_type(
    session,
    responses: dict,
    idx: int = 0,
    __selected: str = None,
    disabled: bool = None,
    _min: int = 0,
    _max: int = 10,
    options: list[str] = None,
    *,
    t=None,
):
    selected = __selected or responses.get(f"select-type-{idx}", "ANSWER")
    items = [
        fh.Select(
            *[fh.Option(k, id=k, title=k, selected=selected == k) for k in QuestionType],
            hx_target=f"#type-{idx}",
            hx_post=f"/forms/question-type?idx={idx}",
            hx_swap="outerHTML",
            id=f"select-type-{idx}",
            title=t("forms.create.type"),
            disabled=disabled,
        )
    ]
    if selected == "SCALE":
        items.append(
            mui.Grid(
                mui.Input(title="Minimum", type="number", inputmode="numeric", value=_min, id="min", disabled=disabled),
                mui.Input(
                    title="Maximum",
                    type="number",
                    inputmode="numeric",
                    value=_max,
                    pattern=r"\d*",
                    id="max",
                    disabled=disabled,
                ),
            )
        )
    if selected == "CHOICE":
        items.append(add_option(idx, 0, disabled=disabled, options=options))
    return mui.DivCentered(*items, id=f"type-{idx}")


@rt("/add-option")
def add_option(idx: int, order: int, disabled: bool = None, options: list[str] = None, *, t=None):
    return fh.Div(
        mui.Input(
            id=f"option-{idx}-{order}",
            hx_post=f"/forms/add-option?idx={idx}&order={order + 1}",
            placeholder=t("forms.create.option", x=idx),
            hx_target=f"#option-{idx}-{order}",
            hx_swap="afterend",
            disabled=disabled,
            value=v.value,
        )
        for v in (options or [Question_Options()])
    )


def get_next(responses: dict, key: str):
    if type(responses[key]) is list:
        return next(responses[key])
    return responses[key]


@rt
def add(session, responses: dict, *, t=None):
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


def get_form(session, event_id: str, feedback: bool = False):
    return Event.maybe_one(
        Event.select(
            session["auth"],
            f'*, form:{"feedback_" if feedback else ""}form_id (*, questions:"Form_Questions" (order, required, question:"Question" (*, options:"Question_Options" (id, value), answer:"Response" (value))))',
        )
        .eq("id", event_id)
        .eq("form.questions.question.answer.event_id", event_id)
        .eq("form.questions.question.answer.user_id", session["id"])
    )


@rt("/{event_id}")
@with_layout(Layout, "Rejestracja na wydarzenie")
def event_form(session, event_id: str):
    f = get_form(session, event_id)
    if not f or not f.form:
        return mui.DivCentered("Podany formularz nie istnieje", back_to_main())
    return form(f)


@rt("/feedback/{event_id}")
@with_layout(Layout, "Feedback z wydarzenia")
def feedback_form(session, event_id: str):
    f = get_form(session, event_id, True)
    if not f or not f.form:
        return mui.DivCentered("Podany formularz nie istnieje", back_to_main())
    if f and f.end_time > datetime.now(TIMEZONE):
        return "Wróć po skończeniu wydarzenia!"

    return form(f, path="submit-feedback")


def save_to_db(session, event, responses, feedback: bool = False):
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
            "filled_form" if not feedback else "feedback_filled": datetime.now(TIMEZONE).isoformat(),
        }
    ).execute()


@rt("/submit/{event}")
def submit(session, event: str, responses: dict):
    try:
        save_to_db(session, event, responses)
    except Exception as ex:
        return mui.DivCentered("Coś poszło nie tak... odśwież stronę i wprowadź odpowiedzi ponownie.")
    return (
        mui.DivCentered(
            "Dzięki za zapis!",
            mui.Button(
                fh.A("Pobierz bilet na wydarzenie", href=f"/tickets/qr?event_id={event}"),
                submit=False,
                cls=mui.ButtonT.primary,
            ),
            "Do wydarzeń plenerowych oraz imprez otrzymasz dodatkowo e-mail organizacyjny parę dni przed wydarzeniem z dokładniejszą lokalizacją - Sprawdź wtedy swoją skrzynkę odbiorczą:",
            mui.Button(session["email"], cls=mui.ButtonT.secondary, submit=False),
            "i potwierdź obecność gdy otrzymasz zaproszenie!",
        ),
        mui.DivFullySpaced(
            fh.A(
                mui.Button(
                    "Strona z deklaracją przyniesienia przedmiotów na wydarzenie",
                    cls=mui.ButtonT.ghost,
                    submit=False,
                ),
                href=f"/contributions/{event}",
            ),
            mui.DivRAligned(back_to_main()),
        ),
    )


@rt("/submit-feedback/{event}")
def submit_feedback(session, event: str, responses: dict):
    try:
        save_to_db(session, event, responses, feedback=True)
    except:
        return mui.DivCentered("Coś poszło nie tak... odśwież stronę i wprowadź odpowiedzi ponownie.")
    return mui.DivCentered("Dzięki za feedback! Zapraszam na następne wydarzenia!"), mui.DivRAligned(back_to_main())
