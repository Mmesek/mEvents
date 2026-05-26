from fasthtml import common as fh
from monsterui import all as mui

from src.components import FormLayout, handle_updating_responses
from src.db import s
from src.generators import QuestionType
from src.models.forms import Form, Question, Question_Options, Response
from src.modules.forms import rt


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


def build_query(**kwargs):
    return "&".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)


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
