from datetime import datetime

from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE, Layout, back_to_main, handle_updating_responses, with_layout
from src.components.app_factory import make_app
from src.models.forms import Response
from src.modules.events import Event
from src.modules.tickets import Attendance

mui.franken_class_map["ul"] = "list-[square] list-inside space-y-2 mb-6 ml-6 text-lg"


rt = make_app("forms")


def form(e: Event, path="submit"):
    return e.form.render(e.id, path, registered=e.tickets)


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
