import os

from fasthtml import common as fh
from mdiscord.http.client import HTTP_Client as HTTP
from monsterui import all as mui

from .events import TIMEZONE, Event, rt

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD = os.getenv("DISCORD_GUILD")


@rt("/discord")
async def discord_events(guild_id: int = DISCORD_GUILD):
    client = HTTP(DISCORD_TOKEN)
    events = await client.list_scheduled_events_for_guild(guild_id)
    await client.close()
    return (
        fh.Title("Nadchodzące wydarzenia Discordowe"),
        mui.DivCentered(mui.H1("Nadchodzące wydarzenia")),
        *[
            Event(
                title=fh.A(f.name, cls=mui.AT.classic, href=f"/forms/?event={f.id}"),
                start_time=f.scheduled_start_time.astimezone(TIMEZONE),
                end_time=f.scheduled_end_time.astimezone(TIMEZONE),
                place=f.entity_metadata.location,
                discord_event=f"https://discord.com/events/{f.guild_id}/{f.id}",
                description=f.description,
                image=f"https://cdn.discordapp.com/guild-events/{f.id}/{f.image}.png?size=1024" if f.image else None,
                # href=f"/forms/?event={f.id}",
            ).info_card()
            for f in sorted(events, key=lambda x: x.scheduled_start_time)
        ],
    )
