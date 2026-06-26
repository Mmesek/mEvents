import datetime
from itertools import chain

from fasthtml import common as fh
from monsterui import all as mui

from src.components import TIMEZONE
from src.components.app_factory import make_app
from src.components.components import with_layout
from src.modules.events import Event

rt = make_app("responses")


def generate(q: dict, date: datetime.datetime):
    avg = 0
    match q.get("type"):
        case "HOUR":
            r = [[int(i) for i in a["value"][0].split(":")] for a in q["answer"]]
            r = [date.replace(hour=h, minute=m) for h, m in r]
            avg = datetime.datetime.fromtimestamp(
                sum(map(datetime.datetime.timestamp, r)) / len(r), datetime.timezone.utc
            ).strftime("%H:%M")
        case "SCALE":
            avg = list(chain.from_iterable([[int(i) for i in a["value"]] for a in q["answer"]]))
            avg = sum(avg) / len(avg)
        case "BOOL":
            avg = len(
                list(
                    chain.from_iterable(
                        [[i for i in a["value"] if i == "on" and a["display_name"]] for a in q["answer"]]
                    )
                )
            )

    for a in q["answer"]:
        if len(a["value"]) == 1:
            a["value"] = a["value"][0]

    return mui.AccordionItem(
        mui.H3(q["title"]),
        mui.Card(
            fh.P(q["description"]),
            fh.P(f"Avg: {avg}") if avg else None,
            fh.Ul(
                *[
                    fh.Li(
                        fh.P(a["display_name"]),
                        fh.Ul(mui.Label(v) for v in a["value"]) if type(a["value"]) is list else mui.Label(a["value"]),
                    )
                    for a in sorted(
                        q["answer"],
                        key=lambda x: int(x["value"] or "")
                        if type(x["value"]) is not list and x["value"].isdigit()
                        else ", ".join(x["value"]) or "",
                    )
                    if a["value"] and a["display_name"]
                ],
                style=mui.ListT.bullet,
            ),
        ),
    )


@rt("/{event_id}")
@with_layout()
def responses(session, event_id: int, user_id: str = None, feedback: bool = False):
    f = (
        Event.select(
            session["auth"],
            f'title, start_time, form:{"feedback_" if feedback else ""}form_id (questions:"Form_Questions" (order, question:"Question" (*, options:"Question_Options" (id, value), answer:"Response" (value, ..."users" (display_name)))))',
        )
        .eq("id", event_id)
        .eq("form.questions.question.answer.event_id", event_id)
        .eq("form.questions.question.answer.users.event_id", event_id)
    )
    if user_id:
        f = f.eq("form.questions.question.answer.user_id", user_id)

    f = (f.maybe_single().execute()).data or {}
    questions = sorted(
        [
            dict(order=q.get("order"), **q.get("question"))
            for q in (f.get("form", {}) or {}).get("questions", {})
            if q.get("question", {}).get("answer")
        ],
        key=lambda x: x["order"],
    )
    date = datetime.datetime.fromisoformat(f["start_time"])
    return mui.Card(mui.Accordion(generate(q, date) for q in questions))
