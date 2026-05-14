from dataclasses import dataclass

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


@dataclass
class Forms:
    title: str
    description: str
    questions: list[Question]
    info: dict
