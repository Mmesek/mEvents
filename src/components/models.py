from uuid import UUID
from src.db import Base
from enum import Enum


class Response(Base):
    user_id: UUID = None


class Form(Base):
    title: str = None
    description: str | None = None
    questions: list | None = None


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


class Question_Options(Base):
    id: int
    question_id: int
    value: str


class Question(Base):
    id: int
    type: QuestionType
    title: str
    description: str | None = None
    allow_multiple_answers: bool | None = None
    min_length: int | None = None
    max_length: int | None = None
    options: list[Question_Options] = None
