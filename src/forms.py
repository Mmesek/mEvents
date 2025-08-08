from dataclasses import dataclass

from src.components import FormSectionDiv
from src.generators import QuestionType
from fasthtml import common as fh


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

    def __post_init__(self):
        self.type = QuestionType.get(self.type)

    def generate(self):
        value = ", ".join([", ".join(i["value"]) for i in self.answer])
        return FormSectionDiv(
            self.type(
                question=self.title,
                question_id=self.id,
                description=self.description,
                **{
                    "max_length": self.max_length,
                    "min_length": self.min_length,
                    "min": self.min_length,
                    "max": self.max_length,
                    "default": value,
                    "value": value,
                    "checked": True if value == "on" else False,
                    "options": [i["value"] for i in self.options],
                },
            ),
            fh.Input(id=f"previous_{self.id}", value=value, hidden=True),
        )


@dataclass
class Forms:
    title: str
    description: str
    questions: list[Question]
    info: dict
