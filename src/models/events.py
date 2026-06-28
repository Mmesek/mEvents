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
    withdrew: datetime | None = None
    authorized_by: str | None = None
    created_at: datetime | None = None
    companions: int | None = None
    left: datetime | None = None
    feedback_filled: datetime | None = None
    display_name: NotSerializable[str | None] = None
    email: NotSerializable[str | None] = None
    event: NotSerializable[dict | None] = None

    def __post_init__(self):
        if not self.display_name:
            return
        name = self.display_name.split(" ", 1)
        if len(name) >= 2:
            self.display_name = f"{name[0]} {name[1][:2]}"

    def event_guests(self, session):
        return Attendance.get(
            Attendance.select(session["auth"], "*, ...users!Attendance_user_id_fkey (display_name)")
            .eq("event_id", self.event_id)
            .eq("users.event_id", self.event_id)
            .filter("withdrew", "is", "null")
            .order("created_at")
        )

    def guest_emails(self, session):
        return Attendance.get(
            Attendance.select(session["auth"], "*, ...users!Attendance_user_id_fkey (display_name, email)")
            .eq("event_id", self.event_id)
            .eq("users.event_id", self.event_id)
            .filter("withdrew", "is", "null")
            .order("created_at")
        )

    def already_verified(self, session):
        return Attendance.maybe_one(
            Attendance.table(session["auth"])
            .select("*")
            .eq("event_id", self.event_id)
            .eq("user_id", self.user_id)
            .not_.is_("arrived", None)
        )

    def last_event(self, session):
        return (
            Attendance.maybe_one(
                Attendance.select(session["auth"], 'arrived, left, event:"Event" (title)')
                .eq("user_id", self.user_id)
                .filter("arrived", "is", "not_null")
                .order("arrived", desc=True)
                .limit(1)
            )
            or self
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

    def guest_emails(self, session):
        if session["id"] == str(self.user_id):
            return Attendance(self.id).guest_emails(session)
        return []
