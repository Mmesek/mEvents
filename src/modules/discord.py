import os

import pytz
from fasthtml import common as fh
from mdiscord.http.client import HTTP_Client as HTTP
from monsterui.all import AT, H1, DivCentered

from src.generators import info_card

from .events import rt

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
            info_card(
                fh.A(f.name, cls=AT.classic, href=f"/forms/?event={f.id}"),
                f"{f.scheduled_start_time.astimezone(pytz.timezone('Europe/Warsaw')).strftime('%H:%M')}",
                f"{f.scheduled_end_time.astimezone(pytz.timezone('Europe/Warsaw')).strftime('%H:%M')}",
                f.scheduled_start_time.astimezone(
                    pytz.timezone("Europe/Warsaw")
                ).date(),
                f.entity_metadata.location,
                discord_event=f"https://discord.com/events/{f.guild_id}/{f.id}",
                description=f.description,
                image=f"https://cdn.discordapp.com/guild-events/{f.id}/{f.image}.png?size=1024"
                if f.image
                else None,
                href=f"/forms/?event={f.id}",
            )
            for f in sorted(events, key=lambda x: x.scheduled_start_time)
        ],
    )
