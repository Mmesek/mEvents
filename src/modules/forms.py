from datetime import datetime

from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE, Layout, back_to_main, handle_updating_responses, with_layout
from src.components.app_factory import make_app
from src.models.forms import Response
from src.modules.events import Event
from src.modules.tickets import Attendance
from src.generators import QuestionType
from src.utils import build_query
from src import components as mu

mui.franken_class_map["ul"] = "list-[square] list-inside space-y-2 mb-6 ml-6 text-lg"


rt = make_app("forms")


def form(e: Event, path="submit"):
    return (
        mui.DivCentered(
            fh.NotStr(
                mui.render_md(
                    "**JESZCZE NIE JESTEŚ ZAPISANY/A NA WYDARZENIE!** Jedynie pytania oznaczone gwiazdką `(*)` są wymagane do zapisu."
                )
            ),
        )
        if not e.tickets
        else None,
        e.form.render(e.id, path),
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


def get_form(session, event_id: str, feedback: bool = False):
    return Event.maybe_one(
        Event.select(
            session["auth"],
            f'*, form:{"feedback_" if feedback else ""}form_id (*, questions:"Form_Questions" (order, required, question:"Question" (*, options:"Question_Options" (id, value), answer:"Response" (value)))), tickets:"Attendance" (user_id, filled_form, feedback_filled)',
        )
        .eq("id", event_id)
        .eq("form.questions.question.answer.event_id", event_id)
        .eq("form.questions.question.answer.user_id", session["id"])
        .eq("tickets.user_id", session["id"])
    )


@rt("/add-answer")
def add_answer(
    responses: dict,
    id: int,
    type_: str,
    required: bool = False,
    min_: int = None,
    max_: int = None,
    value: str = None,
    options: list[str] = None,
    allow_multiple: bool = False,
    event_id: int = None,
    session=None,
):
    responses.pop("event_id", None)
    responses.pop("id", None)
    responses.pop("allow_multiple", None)
    responses.pop("type_", None)
    responses = handle_updating_responses(responses)
    if responses:
        r = [
            {
                "user_id": session["id"],
                "event_id": event_id,
                "question_id": k,
                "value": [v] if type(v) is not list else [i for i in v if i],
            }
            for k, v in responses.items()
            if v
        ]
        Response.table(session["auth"]).upsert(r).execute()
    if not responses or allow_multiple:
        if value:
            value = value.strip() or None
        if options:
            options = [v.strip() or None for v in (options or [])]
        return QuestionType.get(type_)(
            id=id,
            required=required,
            max_length=max_,
            min_length=min_,
            min=min_,
            max=max_,
            default=value,
            value=value,
            checked=value == "on",
            options=options,
            hx_post=f"/forms/add-answer?{build_query(type_=type_, event_id=event_id, id=id, allow_multiple=allow_multiple)}",
            hx_swap="beforeend",
            hx_target=f"#question-{id}",
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
                "value": [v] if type(v) is not list else [i for i in v if i],
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
            "withdrew": None,
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
            mu.Button(
                fh.A("Pobierz bilet na wydarzenie", href=f"/tickets/qr?event_id={event}"),
                submit=False,
                cls=mu.ButtonT.primary,
            ),
            "Do wydarzeń plenerowych oraz imprez otrzymasz dodatkowo e-mail organizacyjny parę dni przed wydarzeniem z dokładniejszą lokalizacją - Sprawdź wtedy swoją skrzynkę odbiorczą:",
            mu.Button(session["email"], cls=mu.ButtonT.secondary, submit=False),
            "i potwierdź obecność gdy otrzymasz zaproszenie!",
        ),
        mui.DivFullySpaced(
            fh.A(
                mu.Button(
                    "Strona z deklaracją przyniesienia przedmiotów na wydarzenie",
                    cls=mu.ButtonT.secondary,
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
