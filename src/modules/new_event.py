from fasthtml import common as fh
from monsterui import all as mui

from src.components import handle_updating_responses

from src.models.forms import Form
from src.components.info import MetaInfo
from src.modules.events import rt, Event
from src import components as mu


@rt
def create(session, t):
    content = mui.DivCentered(
        mui.Card(
            mui.DivCentered(
                mui.H1(
                    mui.Input(
                        id="title",
                        placeholder=t("events.create.title.name"),
                        required=True,
                        title=t("events.create.title.description"),
                    ),
                ),
                cls="required",
            ),
            MetaInfo.edit(
                t,
                (
                    "user",
                    mui.Input(
                        id="org_name",
                        value=session["display_name"].title(),
                        title=t("events.create.org_name.description"),
                    ),
                    False,
                ),
                (
                    "shirt",
                    (
                        mui.Input(
                            id="dresscode",
                            placeholder=t("events.create.dresscode.name"),
                            title=t("events.create.dresscode.description"),
                        ),
                        mui.Switch(
                            id="dresscode_mandatory",
                            title=t("events.create.dresscode_mandatory.description"),
                        ),
                        fh.P(
                            t("events.create.dresscode_mandatory.name"),
                            cls=mui.TextPresets.muted_sm,
                        ),
                    ),
                    False,
                ),
            ),
            mui.DivCentered(
                mui.TextArea(
                    id="description",
                    placeholder=t("events.create.description.default"),
                    title=t("events.create.description.description"),
                )
            ),
            mui.Switch(t("events.create.is_private"), id="private"),
            mui.DivFullySpaced(
                mu.Select(
                    t("events.create.select_form"),
                    *[
                        form_option(f["title"], f["id"])
                        for f in Form.select(session["auth"], "id, title")
                        .eq("is_feedback", False)
                        .order("popularity", desc=True)
                        .execute()
                        .data
                    ],
                    form_option(t("events.create.new_form"), form_id=None),
                    id="form_id",
                    searchable=True,
                    hx_target="#form",
                    hx_swap="innerHTML",
                    placeholder=t("events.create.select_form"),
                ),
                mu.Select(
                    t("events.create.select_feedback_form"),
                    *[
                        form_option(f["title"], f["id"])
                        for f in Form.select(session["auth"], "id, title").eq("is_feedback", True).execute().data
                    ],
                    form_option(t("events.create.no_form"), None),
                    searchable=True,
                    placeholder=t("events.create.select_feedback_form"),
                    id="feedback_form_id",
                ),
            ),
            fh.Div(id="form"),
            mu.Button(t("events.create.add.add"), cls=mu.ButtonT.primary),
        )
    )
    return mui.Container(
        fh.Form(
            mui.DivCentered(
                fh.H1(t("events.create.add.title")),
                t("events.create.add.description"),
                mui.DividerLine(),
            ),
            content,
            cls="space-y-3 mt-4",
            hx_post="/events/add",
        )
    )


def form_option(name: str, form_id: int, selected: bool = False):
    return fh.Option(name, hx_post=f"/forms/new?form_id={form_id}", value=form_id, selected=selected)


@rt
def add(session, responses: dict, *, t=None):
    responses = handle_updating_responses(responses)

    try:
        responses["start_time"] = responses.pop("start_date") + "T" + responses["start_time"] + ":00"
        responses["end_time"] = responses.pop("end_date") + "T" + responses["end_time"] + ":00"
        responses["dresscode_mandatory"] = responses.get("dresscode_mandatory", False) == "on"
        Event.table(session["auth"]).upsert([{"user_id": session["id"], **responses}]).execute()
        responses["form_id"] = int(responses.get("form_id", 0))
        responses["feedback_form_id"] = int(responses.get("feedback_form_id", 0))

        return Event.from_dict(responses).info_card()

    except Exception as ex:
        return mui.DivCentered(t("events.create.add.failed")), mui.DivRAligned(ex)

    return mui.DivCentered(t("events.create.add.success")), mui.DivRAligned("Test")
