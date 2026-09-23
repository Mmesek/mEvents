from src.db import Base

from datetime import datetime


class users(Base):
    display_name: str
    email: str
    event_id: int
    timestamp: datetime
    id: str
