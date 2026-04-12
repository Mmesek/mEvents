import datetime
from fasthtml import common as fh
from monsterui.all import H3, Label, ListT, Card

from src.components.headers import HEADERS
from src.components.components import with_layout
from src.db import s
from src.beforeware import beforeware, translations
from itertools import chain

app, rt = fh.fast_app(hdrs=HEADERS, before=[beforeware, translations])


def generate(q: dict, date: datetime.datetime):
    avg = 0
    match q.get("type"):
        case "HOUR":
            r = [[int(i) for i in a["value"][0].split(":")] for a in q["answer"]]
            r = [date.replace(hour=h, minute=m) for h, m in r]
            avg = datetime.datetime.strftime(
                datetime.datetime.fromtimestamp(sum(map(datetime.datetime.timestamp, r)) / len(r)), "%H:%M"
            )
        case "SCALE":
            avg = list(chain.from_iterable([[int(i) for i in a["value"][0]] for a in q["answer"]]))
            avg = sum(avg) / len(avg)

    for a in q["answer"]:
        if len(a["value"]) == 1:
            a["value"] = a["value"][0]

    return Card(
        H3(q["title"]),
        fh.P(q["description"]),
        fh.P(f"Avg: {avg}") if avg else None,
        fh.Ul(
            *[
                fh.Li(
                    fh.P(a["user"]["display_name"]),
                    fh.Ul(Label(v) for v in a["value"]) if type(a["value"]) is list else Label(a["value"]),
                )
                for a in sorted(
                    q["answer"],
                    key=lambda x: int(x["value"])
                    if type(x["value"]) is not list and x["value"].isdigit()
                    else x["value"],
                )
            ],
            style=ListT.bullet,
        ),
    )


@rt("/{event_id}")
@with_layout()
def responses(event_id: int, user_id: str = None):
    f = (
        s.table("Event")
        .select(
            'title, start_time, form:form_id (questions:"Form_Questions" (order, question:"Question" (*, options:"Question_Options" (id, value), answer:"Response" (value, user:"users" (display_name)))))'
        )
        .eq("id", event_id)
        .eq("form.questions.question.answer.event_id", event_id)
    )
    if user_id:
        f = f.eq("form.questions.question.answer.user_id", user_id)

    f = (f.maybe_single().execute()).data
    questions = sorted(
        [
            dict(order=q.get("order"), **q.get("question"))
            for q in f.get("form", {}).get("questions", {})
            if q.get("question", {}).get("answer")
        ],
        key=lambda x: x["order"],
    )
    date = datetime.datetime.fromisoformat(f["start_time"])
    return [generate(q, date) for q in questions]
