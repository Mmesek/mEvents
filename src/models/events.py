from datetime import datetime
from io import BytesIO
from uuid import UUID

import httpx
from PIL import Image, ImageDraw, ImageFont

from src.components import TIMEZONE
from src.db import Base, NotSerializable
from src.models.forms import Form


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

    def generate_thumbnail(self):
        return render_thumbnail(self.image, self.title, self.start_time.strftime("%Y/%m/%d @ %H:%M"))


def text_w(draw: ImageDraw.ImageDraw, font: ImageFont, t: str) -> int:
    bb = draw.textbbox((0, 0), t, font=font)
    return (bb[2] - bb[0]) if bb else 0


def make_line_overlay(
    w,
    h,
    line: str,
    font,
    draw,
    y_top,
    panel_alpha=140,
    pad_x_ratio=0.04,
    pad_y_ratio=0.03,
    radius_ratio=0.03,
    gap_ratio=0.02,
):
    line_h = font.size + 6

    tw = text_w(draw, font, line)
    left = (w - tw) // 2

    pad_x = int(w * pad_x_ratio)
    pad_y = int(h * pad_y_ratio)

    y_bottom = y_top + line_h + pad_y + int(h * gap_ratio)

    panel = [left - pad_x, y_top - pad_y, left + tw + pad_x, y_bottom]

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    radius = int(min(w, h) * radius_ratio)
    od.rounded_rectangle(panel, radius=radius, fill=(0, 0, 0, panel_alpha))

    return overlay, (left, y_top), y_bottom


def draw_centered_lines_per_line(img, w, h, lines, font, start_y):
    base = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    cur_y = start_y
    for ln in lines:
        overlay, (tx, ty), y_bottom = make_line_overlay(w, h, ln, font, draw, cur_y)
        # draw text onto overlay, so it layers correctly
        od = ImageDraw.Draw(overlay)
        od.text((tx, ty), ln, font=font, fill=(255, 255, 255, 255))
        base = Image.alpha_composite(base, overlay)
        cur_y += font.size + 6

    return base.convert("RGB"), y_bottom + 12


def render_thumbnail(source_image_url: str, lines: str, extra: str):
    resp = httpx.get(source_image_url, timeout=30)
    resp.raise_for_status()

    src_bytes = BytesIO(resp.content)
    img = Image.open(src_bytes).convert("RGB")
    img = img.resize((1200, 700)).crop((0, 0, 1200, 630))

    w, h = img.size

    big_font = ImageFont.load_default(90)
    small_font = ImageFont.load_default(40)

    start_y = h - h // 1.25
    img, end_y = draw_centered_lines_per_line(img, w, h, [lines], big_font, start_y=start_y)

    # end_y = start_y + len([lines]) * (big_font.size + 6)
    img, end_y = draw_centered_lines_per_line(img, w, h, [extra], small_font, start_y=end_y + int(h * 0.02))

    buf = BytesIO()
    img.save(buf, format="WEBP", method=6)
    buf.seek(0)

    return buf
