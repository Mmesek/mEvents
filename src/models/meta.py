from src.db import Base

from datetime import datetime


class users(Base):
    display_name: str
    email: str
    event_id: str
    timestamp: datetime
    id: str
