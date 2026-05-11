from dataclasses import dataclass

import i18n
import monsterui.all as ui
from fasthtml import common as fh

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

    def edit_form(self, session, order: int = None):
        from src.modules.forms import question_type

        order = order or self.order or 0

        return fh.Div(
            fh.Input(id="order", type="hidden", value=order),
            fh.Input(id="original_id", type="hidden", value=self.id),
            ui.Input(
                placeholder=i18n.t("forms.create.question", locale=session.get("locale")),
                id="question",
                required=True,
                cls="required",
                value=self.title,
                disabled=True if self.id else False,
            ),
            ui.TextArea(
                self.description,
                placeholder=i18n.t("forms.create.question_description", locale=session.get("locale")),
                id="description",
                disabled=True if self.id else False,
            ),
            ui.Switch(
                i18n.t("forms.create.is_required", locale=session.get("locale")),
                id="is_required",
                checked=self.required,
            ),
            question_type(session, {}, order, self.type_name),
            ui.DividerLine(),
            id=order,
        )


@dataclass
class Forms:
    title: str
    description: str
    questions: list[Question]
    info: dict
