from dataclasses import dataclass

from components import FormSectionDiv
from generators import QuestionType


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
                    "options": [i["value"] for i in self.options],
                },
            )
        )


@dataclass
class Forms:
    title: str
    description: str
    questions: list[Question]
    info: dict
