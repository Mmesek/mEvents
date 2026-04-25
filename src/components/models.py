from uuid import UUID
from src.db import Base


class Response(Base):
    user_id: UUID = None


class Form(Base):
    pass
