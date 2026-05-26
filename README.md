# Johannite Lectionary Discord Bot

A Discord bot that reads from two CSV lectionary files:

- `data/movable.csv` — movable feasts and Sundays keyed by liturgical name
- `data/non_movable.csv` — fixed-date feasts keyed by calendar date

The bot resolves the relevant date, finds fixed feasts and movable Sundays/feasts, formats the collect, reading, and gospel, then posts them to Discord.

## Commands

- `/readings` — upcoming Sunday by default
- `/readings date:2026-05-31` — readings for a specific civil date
- `/today` — readings for today
- `/next_sunday` — readings for the next Sunday
- `/movables year:2026` — list the calculated movable calendar for a year
- `/fixed month:1 day:6` — show fixed feast for a month/day

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate  # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```env
DISCORD_TOKEN=...
DISCORD_CHANNEL_ID=...
TIMEZONE=America/New_York
```

Then run:

```bash
python bot.py
```

## Discord setup

Create an app and bot at the Discord Developer Portal. Invite the bot using OAuth2 URL Generator with:

- `bot`
- `applications.commands`

Bot permissions:

- Send Messages
- Embed Links
- Read Message History

## CSV expectations

### Movable CSV

Expected columns based on your file:

```csv
Movables,Source,Intent,Collect,Reading Source,Reading,Gospel Source,Gospel,Approved,Notes
```

### Non-movable CSV

Expected columns based on your file:

```csv
Feast,Date,Source,Intent,Collect,Reading Source,Reading,Gospel Source,Gospel,Approved,Notes
```

Dates in the non-movable file can be written like:

```text
January 6
Februrary 14
Sep 29
```

The app includes a small typo-tolerant parser for common month spelling issues like `Februrary`.

## Calendar logic currently implemented

The movable calendar uses Western computus for Easter and derives:

- Advent Sunday through Fourth Sunday in Advent
- Second through Fourth Sundays after Epiphany
- Ash Wednesday
- Sundays in Lent
- Passion Sunday
- Maundy Thursday
- Good Friday
- Easter Vigil
- Easter Day
- Sundays after Easter
- Ascension Day
- Pentecost
- Trinity Sunday
- Corpus Christi
- Sundays after Trinity
- Sunday Next Before Advent
- Day of General Thanksgiving as US Thanksgiving Day

Fixed-date feasts are pulled from `non_movable.csv`.

## Precedence

For a given date, the bot returns all matching items:

1. Fixed-date feasts
2. Movable feasts/Sundays

This avoids silently hiding a fixed saint day that coincides with a Sunday.
