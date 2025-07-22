from db import s

from fasthtml import common as fh
from monsterui.all import Button, ButtonT, DivCentered, DivRAligned, render_md, Theme

from components import FormLayout
from forms import Question
from generators import info_card
from beforeware import beforeware


app, rt = fh.fast_app(hdrs=Theme.orange.headers(), before=beforeware)


def form(user_id, event):
    f = (
        s.table("Form")
        .select(
            '*, questions:"Form_Questions" (order, required, question:"Question" (*, options:"Question_Options" (id, value)))'
        )
        .eq("id", event)
        .single()
        .execute()
        .data
    )
    questions = sorted(
        [
            Question(
                order=q.get("order"), required=q.get("required"), **q.get("question")
            )
            for q in f.get("questions")
        ],
        key=lambda x: x.order,
    )
    answers = {
        i["question_id"]: ",".join(i["value"])
        for i in (
            s.table("Response")
            .select("*")
            .eq("form_id", event)
            .eq("user_id", user_id)
            .execute()
            .data
        )
    }

    content = [q.generate(answers.get(q.id, "")) for q in questions]
    content.append(Button("Zapisz", cls=ButtonT.primary))
    info = info_card(f["title"], **f.get("info")) if f.get("info") else None

    return info, FormLayout(
        "",
        render_md(f["description"]) if f["description"] else None,
        *content,
        destination=f"/form/submit/{event}",
    )


@rt("/{event}")
def event_form(session, event: str):
    return (
        fh.Title("Rejestracja na wydarzenie"),
        DivRAligned(
            "Zalogowano jako:",
            fh.Img(src=session.get("picture"), height="24", width="24"),
            session.get("email"),
        ),
        form(session["id"], event),
    )


@rt("/submit/{event}")
def submit(session, event: str, responses: dict):
    s.table("Response").upsert(
        [
            {
                "user_id": session["id"],
                "form_id": event,
                "question_id": k,
                "value": f"{{{v}}}",
            }
            for k, v in responses.items()
            if v
        ]
    ).execute()

    return DivCentered(
        f"Dzięki za zapis! Sprawdź swojego e-maila {session['email']} i potwierdź obecność gdy otrzymasz zaproszenie!"
    )
