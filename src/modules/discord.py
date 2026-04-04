import os

import pytz
from fasthtml import common as fh
from mdiscord.http.client import HTTP_Client as HTTP
from monsterui.all import AT, H1, DivCentered

from .events import rt
from .events import Event

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD = os.getenv("DISCORD_GUILD")


@rt("/discord")
async def discord_events(guild_id: int = DISCORD_GUILD):
    client = HTTP(DISCORD_TOKEN)
    events = await client.list_scheduled_events_for_guild(guild_id)
    await client.close()
    return (
        fh.Title("Nadchodzące wydarzenia Discordowe"),
        DivCentered(H1("Nadchodzące wydarzenia")),
        *[
            Event(
                title=fh.A(f.name, cls=AT.classic, href=f"/forms/?event={f.id}"),
                start_time=f"{f.scheduled_start_time.astimezone(pytz.timezone('Europe/Warsaw'))}",
                end_time=f"{f.scheduled_end_time.astimezone(pytz.timezone('Europe/Warsaw'))}",
                place=f.entity_metadata.location,
                discord_event=f"https://discord.com/events/{f.guild_id}/{f.id}",
                description=f.description,
                image=f"https://cdn.discordapp.com/guild-events/{f.id}/{f.image}.png?size=1024" if f.image else None,
                # href=f"/forms/?event={f.id}",
            ).info_card()
            for f in sorted(events, key=lambda x: x.scheduled_start_time)
        ],
    )
