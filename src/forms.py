from dataclasses import dataclass

import i18n
import monsterui.all as ui
from fasthtml import common as fh

from src.components import FormSectionDiv
from src.generators import QuestionType


@dataclass
class Question:
    id: int = None
    title: str = None
    type: str = None
    kwargs: dict = None
    order: int = None
    required: bool = False
    max_length: int = None
    min_length: int = None
    description: str = None
    allow_multiple_answer: bool = None
    options: dict = None
    answer: list[dict] = None
    type_name: str = None

    def __post_init__(self):
        self.type_name = self.type
        self.type = QuestionType.get(self.type)

    def generate(self, event_id: int = None):
        value = ", ".join([", ".join(i["value"]) for i in self.answer])
        return FormSectionDiv(
            self.type(
                question=self.title,
                question_id=self.id,
                description=self.description,
                required=self.required,
                max_length=self.max_length,
                min_length=self.min_length,
                min=self.min_length,
                max=self.max_length,
                default=value,
                value=value,
                checked=value == "on",
                options=[i["value"] for i in self.options],
                hx_post=f"/forms/save/{event_id}" if self.type_name != "BOOL" else None,
            ),
            fh.Input(id=f"previous_{self.id}", value=value, hidden=True),
        )

    def edit_form(self, session):
        from src.modules.forms import question_type

        return fh.Div(
            fh.Input(id="order", type="hidden", value=self.order),
            ui.Input(
                placeholder=i18n.t("forms.create.question", locale=session.get("locale")),
                id="question",
                required=True,
                cls="required",
                value=self.title,
            ),
            ui.TextArea(
                self.description,
                placeholder=i18n.t("forms.create.question_description", locale=session.get("locale")),
                id="description",
            ),
            ui.Switch(
                i18n.t("forms.create.is_required", locale=session.get("locale")),
                id="is_required",
                checked=self.required,
            ),
            question_type(session, {}, self.id, self.type_name),
            ui.DividerLine(),
            id=self.id,
        )


@dataclass
class Forms:
    title: str
    description: str
    questions: list[Question]
    info: dict
