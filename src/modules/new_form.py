from fasthtml import common as fh
from monsterui import all as mui

from src.components import FormLayout
from src.components.app_factory import make_app
from src.db import s
from src.models.forms import Form, Question, Question_Options, QuestionType as QT
from src.utils import get_next
from src.generators import QuestionType
from src import components as mu

rt = make_app("forms-api")


@rt("/new")
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
            mu.Button(
                t("forms.create.add_question"),
                hx_target="#questions-list",
                hx_post="/forms-api/add-question",
                hx_swap="beforeend",
            ),
            fh.Div(
                fh.Label(t("events.create.select_form")),
                get_questions(session),
            ),
        ),
        mu.Button(t("forms.create.submit"), cls=mu.ButtonT.primary),
        cls="space-y-4",
        destination="/forms-api/add",
    )


def get_questions(session, idx=None):
    q = Question.select(session["auth"], "id, title").execute().data
    cls = fh if not idx else mui
    return cls.Select(
        *[
            fh.Option(
                f["title"],
                hx_post=f"/forms-api/add-question?question_id={f['id']}" if not idx else None,
                selected=f["id"] == idx,
                value=f["id"],
            )
            for f in q
        ],
        id="original_id" if idx else None,
        searchable=True,
        hx_target="#questions-list" if not idx else None,
        hx_swap="beforeend" if not idx else None,
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
        return res.edit_form(session, order + 1, questions_select=get_questions(session, question_id))
    return Question().edit_form(session, order + 1)


@rt("/question-type")
def question_type(
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
            hx_post=f"/forms-api/question-type?idx={idx}",
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
            hx_post=f"/forms-api/add-option?idx={idx}&order={order + 1}",
            placeholder=t("forms.create.option", x=idx),
            hx_target=f"#option-{idx}-{order}",
            hx_swap="afterend",
            disabled=disabled,
            value=v.value,
        )
        for v in (options or [Question_Options()])
    )


@rt
def add(session, responses: dict, *, t=None):
    questions = []
    if type(responses["order"]) is not list:
        responses["order"] = [responses["order"]]
        responses["question"] = [responses.get("question")]
        responses["description"] = [responses.get("description")]
        responses["allow_multiple"] = [responses.get("allow_multiple")]
        responses["original_id"] = [responses["original_id"]]
    responses["question"] = iter(responses.get("question", []))
    responses["description"] = iter(responses.get("description", []))
    responses["allow_multiple"] = iter(responses.get("allow_multiple", []))
    for o, idx in zip(responses["order"], responses["original_id"] or [None] * len(responses["order"]), strict=True):
        if f"select-type-{o}" not in responses:
            responses[f"select-type-{o}"] = "INPUT"
        q = Question(idx or None)
        if not q.id:
            q.type = getattr(QT, responses[f"select-type-{o}"]).value
            q.title = next(responses["question"], None)
            q.description = next(responses["description"], None)
            q.allow_multiple_answers = next(responses["allow_multiple"], None)
        if responses[f"select-type-{o}"] == "SCALE":
            q.min_length = int(get_next(responses, "min"))
            q.max_length = int(get_next(responses, "max"))
        if responses[f"select-type-{o}"] == "CHOICE":
            q.options = []
            for k, v in responses.items():
                if k.startswith(f"option-{o}") and v:
                    q.options.append(v)
        questions.append(q.to_dict())
    res = (
        s.auth(session["auth"])
        .rpc(
            "create_form_with_questions",
            {"title": responses["form-title"], "description": responses["form-description"], "questions": questions},
        )
        .execute()
    )

    return t("forms.create.success")
