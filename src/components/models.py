from uuid import UUID
from src.db import Base
from enum import Enum
import fasthtml.common as fh
import monsterui.all as mui

from src.components import FormSectionDiv, FormLayout, back_to_main
from src.modules.tickets import Attendance
from src.generators import QuestionType as type_registry
import i18n
import mistletoe


class Response(Base):
    user_id: UUID = None
    value: list[str] = None


class QuestionType(Enum):
    ANSWER = "ANSWER"
    INPUT = "INPUT"
    LONG_INPUT = "LONG_INPUT"
    TEXT = "TEXT"
    CHOICE = "CHOICE"
    HOUR = "HOUR"
    DATE = "DATE"
    SCALE = "SCALE"
    BOOL = "BOOL"
    DATETIME = "DATETIME"

    def __call__(self, **kwargs):
        return type_registry.get(self.value)(**kwargs)


class Question_Options(Base):
    id: int | None = None
    question_id: int | None = None
    value: str | None = None


class Question(Base):
    id: int | None = None
    type: QuestionType | None = QuestionType.ANSWER
    title: str | None = None
    description: str | None = None
    allow_multiple_answers: bool | None = None
    min_length: int | None = None
    max_length: int | None = None
    options: list[Question_Options] = None
    answer: list[Response] = None

    def generate(self, event_id: int = None, required: bool = False):
        from src.modules.forms import add_answer

        return FormSectionDiv(
            mui.H3(self.title, cls=mui.TextPresets.muted_sm + ("required" if required else "")),
            fh.NotStr(mistletoe.markdown(self.description.strip())) if self.description else None,
            fh.Div(
                *[
                    add_answer(
                        {},
                        self.id,
                        self.type.value,
                        required,
                        self.min_length,
                        self.max_length,
                        i,
                        [i],
                        self.allow_multiple_answers,
                        event_id=event_id,
                    )
                    for i in ((self.answer or [Response()])[0].value or [""])
                ],
                id=f"question-{self.id}",
            ),
            fh.Input(id=f"previous_{self.id}", value=[i.value for i in self.answer], hidden=True),
        )

    def edit_form(self, session, order: int = None, required: bool = None):
        from src.modules.forms import question_type

        return fh.Div(
            fh.Input(id="order", type="hidden", value=order),
            fh.Input(id="original_id", type="hidden", value=self.id),
            mui.DivHStacked(
                mui.Switch(
                    i18n.t("forms.create.is_required", locale=session.get("locale")),
                    id="is_required",
                    checked=required,
                    disabled=bool(self.id),
                ),
                mui.Input(
                    placeholder=i18n.t("forms.create.question", locale=session.get("locale")),
                    id="question",
                    required=True,
                    cls="required",
                    value=self.title,
                    disabled=bool(self.id),
                ),
            ),
            mui.TextArea(
                self.description,
                placeholder=i18n.t("forms.create.question_description", locale=session.get("locale")),
                id="description",
                disabled=bool(self.id),
            ),
            question_type(session, {}, order, self.type.value, disabled=bool(self.id), options=self.options or []),
            mui.DividerLine(),
            id=order,
        )


class Form_Questions(Base):
    order: int
    required: bool
    question: Question


class Form(Base):
    title: str = None
    description: str | None = None
    questions: list[Form_Questions] = None

    def render(self, event_id, path="submit", registered: list["Attendance"] = None):
        content = [q.question.generate(event_id, q.required) for q in sorted(self.questions, key=lambda x: x.order)]
        # registered = all(q.question.answer for q in self.questions if q.required)

        if not content:
            content.append(back_to_main())
        else:
            content.append(mui.Button("Zapisz", cls=mui.ButtonT.primary))

        return (
            mui.DivCentered(
                fh.NotStr(
                    mui.render_md(
                        "**JESZCZE NIE JESTEŚ ZAPISANY/A NA WYDARZENIE!** Jedynie pytania oznaczone gwiazdką `(*)` są wymagane do zapisu."
                    )
                ),
            )
            if not registered
            else None,
            fh.Div(
                fh.P("Jeśli nie masz odpowiedzi na dane pytanie, pozostaw pole puste, chyba że jest wymagane."),
                fh.P("Formularz możesz edytować w dowolnym momencie korzystając z tej samej strony."),
            ),
            mui.DividerLine(),
            mui.DivCentered(
                mui.render_md(self.description) if self.description else None, style="max-width: 100em; min-width: 35%"
            ),
            mui.DividerLine(),
            mui.Form(*content, cls="space-y-3 mt-4", hx_post=f"/forms/{path}/{event_id}"),
        )
