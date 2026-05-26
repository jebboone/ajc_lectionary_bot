\
from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from lectionary import Lectionary, format_reading, split_discord_message


load_dotenv()

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DISCORD_CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")
MOVABLE_CSV = os.getenv("MOVABLE_CSV", "data/movable.csv")
NON_MOVABLE_CSV = os.getenv("NON_MOVABLE_CSV", "data/non_movable.csv")

POST_WEEKDAY = os.getenv("POST_WEEKDAY", "MON").upper()
POST_HOUR = int(os.getenv("POST_HOUR", "9"))
POST_MINUTE = int(os.getenv("POST_MINUTE", "0"))

tz = ZoneInfo(TIMEZONE)
lectionary = Lectionary(MOVABLE_CSV, NON_MOVABLE_CSV)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler(timezone=TIMEZONE)


def friendly_date(d: date) -> str:
    return d.strftime("%A, %B %d, %Y").replace(" 0", " ")


def parse_iso_date(value: str | None) -> date:
    if not value:
        return lectionary.next_sunday(datetime.now(tz).date())
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise app_commands.AppCommandError("Use date format YYYY-MM-DD, for example 2026-05-31.")


async def send_readings(destination, target: date, quiet_if_missing: bool = False):
    readings = lectionary.readings_for_date(target)
    if not readings:
        message = f"No readings found for {friendly_date(target)}."
        if not quiet_if_missing:
            await destination.send(message) if hasattr(destination, "send") else await destination.response.send_message(message)
        return

    header = f"## Readings for {friendly_date(target)}"
    if hasattr(destination, "send"):
        await destination.send(header)
        send = destination.send
    else:
        await destination.response.send_message(header)
        send = destination.followup.send

    for item in readings:
        body = format_reading(item).replace("%-d", "%d")
        for chunk in split_discord_message(body):
            await send(chunk)


@bot.event
async def on_ready():
    await bot.tree.sync()
    if not scheduler.running:
        scheduler.start()
    print(f"Logged in as {bot.user}")


@bot.tree.command(name="readings", description="Get lectionary readings. Defaults to the upcoming Sunday.")
@app_commands.describe(date_value="Optional date in YYYY-MM-DD format")
async def readings(interaction: discord.Interaction, date_value: str | None = None):
    try:
        target = parse_iso_date(date_value)
    except app_commands.AppCommandError as exc:
        await interaction.response.send_message(str(exc), ephemeral=True)
        return
    await send_readings(interaction, target)


def nearest_reading_date(start_date: date, window_days: int = 7) -> date:
    if lectionary.readings_for_date(start_date):
        return start_date

    for offset in range(1, window_days + 1):
        future = start_date + timedelta(days=offset)
        past = start_date - timedelta(days=offset)

        if lectionary.readings_for_date(future):
            return future

        if lectionary.readings_for_date(past):
            return past

    return lectionary.next_sunday(start_date)


@bot.tree.command(name="today", description="Get the nearest lectionary readings to today.")
async def today(interaction: discord.Interaction):
    target = nearest_reading_date(datetime.now(tz).date())
    await send_readings(interaction, target)


@bot.tree.command(name="next_sunday", description="Get the next Sunday's lectionary readings.")
async def next_sunday(interaction: discord.Interaction):
    await send_readings(interaction, lectionary.next_sunday(datetime.now(tz).date()))


@bot.tree.command(name="fixed", description="Look up a fixed feast by month/day.")
@app_commands.describe(month="Month number, 1-12", day="Day of month")
async def fixed(interaction: discord.Interaction, month: int, day: int):
    try:
        target = date(datetime.now(tz).year, month, day)
    except ValueError:
        await interaction.response.send_message("Invalid month/day.", ephemeral=True)
        return
    readings = lectionary.fixed_for_date(target)
    if not readings:
        await interaction.response.send_message(f"No fixed feast found for {month}/{day}.", ephemeral=True)
        return
    await interaction.response.send_message(f"Fixed feast(s) for {month}/{day}:")
    for item in readings:
        for chunk in split_discord_message(format_reading(item)):
            await interaction.followup.send(chunk)


@bot.tree.command(name="movables", description="List the calculated movable calendar for a year.")
@app_commands.describe(year="Civil year, for example 2026")
async def movables(interaction: discord.Interaction, year: int):
    if year < 1900 or year > 2200:
        await interaction.response.send_message("Use a year between 1900 and 2200.", ephemeral=True)
        return

    rows = lectionary.calculated_calendar(year)
    lines = []
    for day, title, has_row in rows:
        mark = "✓" if has_row else "missing CSV row"
        lines.append(f"{day.isoformat()} — {title} ({mark})")

    text = "\n".join(lines)
    await interaction.response.send_message(f"Movable calendar for {year}:")
    for chunk in split_discord_message(text):
        await interaction.followup.send(f"```text\n{chunk}\n```")


async def scheduled_weekly_post():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel is None:
        channel = await bot.fetch_channel(DISCORD_CHANNEL_ID)
    target = lectionary.next_sunday(datetime.now(tz).date())
    await send_readings(channel, target, quiet_if_missing=True)


scheduler.add_job(
    scheduled_weekly_post,
    "cron",
    day_of_week=POST_WEEKDAY.lower(),
    hour=POST_HOUR,
    minute=POST_MINUTE,
)

bot.run(DISCORD_TOKEN)
