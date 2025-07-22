from fasthtml import common as fh
from monsterui.all import (
    AT,
    H1,
    Button,
    ButtonT,
    Card,
    DivCentered,
    DivLAligned,
    DivRAligned,
    Theme,
    UkIconLink,
    render_md,
)

from components import FormLayout
from db import s
from forms import Question
from generators import info_card
from login import app as login_app

hdrs = Theme.orange.headers()


def user_auth_before(req, sess):
    auth = req.scope["email"] = sess.get("email", None)
    if not auth:
        return fh.RedirectResponse("/login", 303)


beforeware = fh.Beforeware(
    user_auth_before,
    skip=[
        r"/favicon\.ico",
        r"/static/.*",
        r".*\.css",
        r".*\.js",
        "/login",
        "/",
        "/events",
    ],
)

# Create your app with the theme
app, rt = fh.fast_app(
    hdrs=hdrs, routes=[fh.Mount("/login", login_app)], before=beforeware
)


@rt("/events")
def events():
    forms = s.table("Form").select("*").execute().data

    socials = (
        ("github", "https://github.com/Mmesek/mEvents"),
        ("messages-square", "https://discord.com"),
    )

    return (
        fh.Title("Nadchodzące wydarzenia"),
        DivCentered(H1("Nadchodzące wydarzenia")),
        *[
            info_card(
                fh.A(f["title"], cls=AT.classic, href=f"/form/{f['id']}"),
                # **f.info,
            )
            for f in forms
            # if f.info
        ],
        Card(
            footer=DivCentered(
                DivLAligned(*[UkIconLink(icon, href=url) for icon, url in socials])
            ),
        ),
    )


@rt("/")
def index():
    return events()


def form(user_id, event):
    f = (
        s.table("Form")
        .select('*, "Form_Questions" (*, "Question_Options" (*))')
        .eq("id", event)
        .single()
        .execute()
        .data
    )
    questions = [Question(**q) for q in f.get("Question")]
    answers = {
        i["question_id"]: i["value"]
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
        destination=f"/submit/{event}",
    )


@rt("/form/{event}")
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
                "value": v,
            }
            for k, v in responses.items()
            if v
        ]
    ).execute()

    return DivCentered(
        f"Dzięki za zapis! Sprawdź swojego e-maila {session['email']} i potwierdź obecność gdy otrzymasz zaproszenie!"
    )


def require_login(func):
    def wrapped(session, *args, **kwargs):
        if not session.get("email"):
            return fh.Redirect("/login")
        return func(session, *args, **kwargs)

    return wrapped


if __name__ == "__main__":
    fh.serve()
