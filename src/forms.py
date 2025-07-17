from dataclasses import dataclass

from components import FormSectionDiv


@dataclass
class Question:
    id: int = None
    question: str = None
    type: str = None
    kwargs: dict = None
    description: str = None

    def generate(self):
        return FormSectionDiv(
            self.type(
                question=self.question,
                question_id=self.id,
                description=self.description,
                **(self.kwargs or {}),
            )
        )


@dataclass
class Forms:
    title: str
    description: str
    questions: list[Question]
    info: dict
