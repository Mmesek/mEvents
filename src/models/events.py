from uuid import UUID
from datetime import datetime
from src.models.forms import Form
from src.db import Base, NotSerializable
from src.components import TIMEZONE


class Attendance(Base):
    event_id: int | None = None
    user_id: str | None = None
    filled_form: str | None = None
    downloaded_ticket: str | None = None
    arrived: datetime | None = None
    withdrew: str | None = None
    authorized_by: str | None = None
    created_at: datetime | None = None
    companions: int | None = None
    left: datetime | None = None
    feedback_filled: datetime | None = None
    display_name: NotSerializable[str | None] = None
    event: NotSerializable[dict | None] = None

    def event_guests(self, session):
        return (
            Attendance.select(session["auth"], "*, ...users!Attendance_user_id_fkey (display_name)")
            .eq("event_id", self.event_id)
            .eq("users.event_id", self.event_id)
            .filter("withdrew", "is", "null")
            .order("created_at")
            .execute()
            .data
        )

    def already_verified(self, session):
        return (
            Attendance.table(session["auth"])
            .select("*")
            .eq("event_id", self.event_id)
            .eq("user_id", self.user_id)
            .not_.is_("arrived", None)
            .maybe_single()
            .execute()
        )

    def last_event(self, session):
        return Attendance.get_one(
            Attendance.select(session["auth"], 'arrived, left, event:"Event" (title)')
            .eq("user_id", self.user_id)
            .filter("arrived", "is", "not_null")
            .order("arrived", desc=True)
            .limit(1)
        )


class Event(Base):
    id: int = None
    title: str = None
    description: str | None = None
    form_id: int | None = None
    feedback_form_id: int | None = None
    user_id: UUID = None
    place: str | None = None
    start_time: datetime = None
    end_time: datetime | None = None
    theme: str | None = None
    dresscode: str | None = None
    dresscode_mandatory: bool | None = None
    discord_event: str | None = None
    wrap: str | None = None
    image: str | None = None
    tickets: NotSerializable[list[Attendance]] = None
    org_name: str | None = None
    private: bool | None = None
    form: NotSerializable[Form | None] = None

    def __post_init__(self):
        self.start_time = self.start_time.astimezone(TIMEZONE)
        self.end_time = self.end_time.astimezone(TIMEZONE)

    @property
    def event_started(self):
        return self.start_time < datetime.now(TIMEZONE)

    def guests(self, session):
        return Attendance(self.id).event_guests(session)
