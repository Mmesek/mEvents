import msgspec

from fasthtml import common as fh
from monsterui import all as mui

from src.components import (
    icon_text,
    right_icon_text,
)


ICONS = {
    "start_time": "clock",
    "end_time": "clock-10",
    "start_date": "calendar",
    "end_date": "calendar",
    "place": "pin",
    "users": "users",
    "org_name": "user",
    "theme": "palette",
    "dresscode": "shirt",
}

FIELD_NAMES = {"users": "Zapisanych", "org_name": "Organizator", "theme": "Motyw", "dresscode": "Styl Ubioru"}
FIELD_ORDER = ["start_time", "end_time", "start_date", "end_date", "place", "users", "org_name", "theme", "dresscode"]
FIELDS_REQUIRED = {"start_time", "start_date", "end_date", "place"}
FIELD_TYPES = {"start_time": "time", "end_time": "time", "start_date": "date", "end_date": "date"}


def fmt_field_name(name: str, value: str):
    f = FIELD_NAMES.get(name)
    return f"**{f}**: {value}" if f else value


def make_grid(fields):
    return mui.Grid(
        (
            right_icon_text(x[0], x[1], "", x[2]) if n % 2 else icon_text(x[0], x[1], "", x[2])
            for n, x in enumerate(x for x in fields if x)
        ),
        cols=2,
        cls="gap-1 items-center justify-center",
    )


class MetaInfo(msgspec.Struct):
    start_time: str
    end_time: str
    start_date: str
    end_date: str
    place: str
    users: str
    org_name: str
    theme: str
    dresscode: str

    def render(self):
        fields = []

        for k in FIELD_ORDER:
            if v := getattr(self, k):
                fields.append((ICONS.get(k), fmt_field_name(k, v), False))
        return make_grid(fields)

    @classmethod
    def edit(cls, t, *extra):
        return make_grid(
            [
                *[
                    (
                        ICONS.get(k),
                        mui.Input(
                            type=FIELD_TYPES.get(k),
                            placeholder=t(f"events.create.{k}.name"),
                            id=k,
                            required=k in FIELDS_REQUIRED,
                            title=t(f"events.create.{k}.description"),
                        ),
                        "required" if k in FIELDS_REQUIRED else "",
                    )
                    for k in FIELD_ORDER
                    if k not in {"users", "org_name", "dresscode"}
                ],
                *extra,
            ]
        )
