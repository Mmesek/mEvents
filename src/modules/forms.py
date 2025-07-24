from fasthtml import common as fh
from monsterui.all import Button, ButtonT, DivCentered, DivRAligned, Theme, render_md

from src.beforeware import beforeware
from src.components import FormLayout
from src.db import s
from src.forms import Question
from src.generators import info_card

app, rt = fh.fast_app(hdrs=Theme.orange.headers(), before=beforeware)


def form(user_id, event_id):
    f = (
        s.table("Event")
        .select(
            'form:form_id (*, questions:"Form_Questions" (order, required, question:"Question" (*, options:"Question_Options" (id, value), answer:"Response" (value))))'
        )
        .eq("id", event_id)
        .eq("form.questions.question.answer.event_id", event_id)
        .eq("form.questions.question.answer.user_id", user_id)
        .single()
        .execute()
        .data
    ).get("form", {})
    questions = sorted(
        [
            Question(
                order=q.get("order"), required=q.get("required"), **q.get("question")
            )
            for q in f.get("questions")
        ],
        key=lambda x: x.order,
    )
    content = [q.generate() for q in questions]
    content.append(Button("Zapisz", cls=ButtonT.primary))
    info = info_card(f["title"], **f.get("info")) if f.get("info") else None

    return info, FormLayout(
        "",
        render_md(f["description"]) if f["description"] else None,
        *content,
        destination=f"/forms/submit/{event_id}",
    )


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
        return DivCentered(
            "Coś poszło nie tak... odśwież stronę i wprowadź odpowiedzi ponownie."
        )

    return DivCentered(
        f"Dzięki za zapis! Sprawdź swojego e-maila {session['email']} i potwierdź obecność gdy otrzymasz zaproszenie!"
    )
