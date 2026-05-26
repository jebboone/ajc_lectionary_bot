\
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional


MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "februrary": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


@dataclass(frozen=True)
class Reading:
    title: str
    kind: str  # "fixed" or "movable"
    source: str = ""
    intent: str = ""
    collect: str = ""
    reading_source: str = ""
    reading: str = ""
    gospel_source: str = ""
    gospel: str = ""
    approved: str = ""
    notes: str = ""
    date_label: str = ""


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", "\n").strip()
    if text.lower() == "nan":
        return ""
    return re.sub(r"[ \t]+", " ", text)


def normalize_key(value: str) -> str:
    value = clean(value).lower()
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_month_day(value: str, year: int) -> Optional[date]:
    """Parse fixed dates like 'January 6' or common variants."""
    text = clean(value).lower().replace(",", " ")
    text = re.sub(r"\s+", " ", text).strip()
    match = re.match(r"([a-z]+)\s+(\d{1,2})$", text)
    if not match:
        return None
    month_name, day_text = match.groups()
    month = MONTHS.get(month_name)
    if not month:
        return None
    return date(year, month, int(day_text))


def western_easter(year: int) -> date:
    """Gregorian Easter date using the Meeus/Jones/Butcher algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def sunday_on_or_before(d: date) -> date:
    return d - timedelta(days=(d.weekday() + 1) % 7)


def sunday_on_or_after(d: date) -> date:
    return d + timedelta(days=(6 - d.weekday()) % 7)


def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    first_match = first + timedelta(days=(weekday - first.weekday()) % 7)
    return first_match + timedelta(days=7 * (n - 1))


def advent_sunday(year: int) -> date:
    # First Sunday of Advent is the Sunday on or before Dec 3.
    return sunday_on_or_before(date(year, 12, 3))


def calculated_movables(year: int) -> dict[date, list[str]]:
    easter = western_easter(year)
    result: dict[date, list[str]] = {}

    def add(day: date, title: str) -> None:
        result.setdefault(day, []).append(title)

    # Advent, calculated for the civil year.
    adv1 = advent_sunday(year)
    advent_titles = [
        "Advent Sunday",
        "The Second Sunday In Advent",
        "The Third Sunday In Advent",
        "The Fourth Sunday in Advent",
    ]
    for i, title in enumerate(advent_titles):
        add(adv1 + timedelta(days=7 * i), title)

    # Epiphany Sundays after Jan 6. The CSV begins at "Second Sunday After Epiphany".
    epiphany = date(year, 1, 6)
    first_after_epiphany = sunday_on_or_after(epiphany + timedelta(days=1))
    epiphany_titles = [
        "The Second Sunday After Epiphany",
        "Third Sunday After Epiphany",
        "Fourth Sunday after Epiphany",
    ]
    for offset, title in enumerate(epiphany_titles, start=1):
        add(first_after_epiphany + timedelta(days=7 * offset), title)

    # Lent and Holy Week.
    add(easter - timedelta(days=46), "Ash Wednesday")
    add(easter - timedelta(days=42), "First Sunday in Lent")
    add(easter - timedelta(days=35), "Second Sunday in Lent")
    add(easter - timedelta(days=28), "Third Sunday in Lent")
    add(easter - timedelta(days=21), "Fourth Sunday in Lent")
    add(easter - timedelta(days=14), "Passion Sunday")
    add(easter - timedelta(days=3), "Maundy Thursday")
    add(easter - timedelta(days=2), "Good Friday")
    add(easter - timedelta(days=1), "Easter Vigil")
    add(easter, "Easter Day")

    after_easter_titles = [
        "The First Sunday After Easter",
        "The Second Sunday After Easter",
        "The Third Sunday After Easter",
        "The Fourth Sunday After Easter",
        "The Fifth Sunday After Easter",
    ]
    for i, title in enumerate(after_easter_titles, start=1):
        add(easter + timedelta(days=7 * i), title)

    add(easter + timedelta(days=39), "Ascension Day")
    add(easter + timedelta(days=49), "Pentecost")
    trinity = easter + timedelta(days=56)
    add(trinity, "Trinity Sunday")
    add(easter + timedelta(days=60), "Corpus Christi")

    # Trinity season, until the Sunday before next Advent.
    next_advent = advent_sunday(year)
    sunday_before_advent = next_advent - timedelta(days=7)
    add(sunday_before_advent, "The Sunday Next Before Advent")

    trinity_titles = [
        "The First Sunday After Trinity",
        "The Second Sunday After Trinity",
        "The Third Sunday After Trinity",
        "The Fourth Sunday After Trinity",
        "The Fifth Sunday After Trinity",
        "The Sixth Sunday After Trinity",
        "The Seventh Sunday After Trinity",
        "The Eighth Sunday After Trinity",
        "The Ninth Sunday After Trinity",
        "The Tenth Sunday After Trinity",
        "The Eleventh Sunday After Trinity",
        "The Twelfth Sunday After Trinity",
        "The Thirteenth Sunday After Trinity",
        "The Fourteenth Sunday After Trinity",
        "The Fifteenth Sunday After Trinity",
        "The Sixteenth Sunday After Trinity",
        "The Seventeenth Sunday After Trinity",
        "The Eighteenth Sunday After Trinity",
        "The Nineteenth Sunday After Trinity",
        "The Twentieth Sunday After Trinity",
        "The Twenty-First Sunday After Trinity",
        "The Twenty-Second Sunday After Trinity",
        "Twenty-Third Sunday After Trinity",
        "Twenty-fourth Sunday After Trinity",
        "The Twenty-Fifth Sunday After Trinity",
    ]
    first_after_trinity = trinity + timedelta(days=7)
    for i, title in enumerate(trinity_titles):
        day = first_after_trinity + timedelta(days=7 * i)
        if day < sunday_before_advent:
            add(day, title)

    # US Thanksgiving: fourth Thursday in November.
    add(nth_weekday_of_month(year, 11, 3, 4), "Day of General Thanksgiving")

    return result


class Lectionary:
    def __init__(self, movable_csv: str | Path, non_movable_csv: str | Path):
        self.movable_csv = Path(movable_csv)
        self.non_movable_csv = Path(non_movable_csv)
        self.movable_rows = self._load_movable()
        self.fixed_rows = self._load_fixed()

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return [{k: clean(v) for k, v in row.items()} for row in csv.DictReader(f)]

    def _row_to_reading(self, row: dict[str, str], title_column: str, kind: str) -> Reading:
        return Reading(
            title=clean(row.get(title_column, "")),
            kind=kind,
            source=clean(row.get("Source")),
            intent=clean(row.get("Intent")),
            collect=clean(row.get("Collect")),
            reading_source=clean(row.get("Reading Source")),
            reading=clean(row.get("Reading")),
            gospel_source=clean(row.get("Gospel Source")),
            gospel=clean(row.get("Gospel")),
            approved=clean(row.get("Approved")),
            notes=clean(row.get("Notes")),
            date_label=clean(row.get("Date")),
        )

    def _load_movable(self) -> dict[str, Reading]:
        rows = self._read_csv(self.movable_csv)
        readings: dict[str, Reading] = {}
        for row in rows:
            reading = self._row_to_reading(row, "Movables", "movable")
            if reading.title:
                readings[normalize_key(reading.title)] = reading
        return readings

    def _load_fixed(self) -> list[Reading]:
        rows = self._read_csv(self.non_movable_csv)
        readings = []
        for row in rows:
            reading = self._row_to_reading(row, "Feast", "fixed")
            if reading.title and reading.date_label:
                readings.append(reading)
        return readings

    def fixed_for_date(self, target: date) -> list[Reading]:
        matches = []
        for reading in self.fixed_rows:
            parsed = parse_month_day(reading.date_label, target.year)
            if parsed == target:
                matches.append(reading)
        return matches

    def movable_titles_for_date(self, target: date) -> list[str]:
        titles = calculated_movables(target.year).get(target, [])
        # Advent dates in late December can belong to the same civil year already.
        return titles

    def movable_for_date(self, target: date) -> list[Reading]:
        matches = []
        for title in self.movable_titles_for_date(target):
            row = self.movable_rows.get(normalize_key(title))
            if row:
                matches.append(row)
        return matches

    def readings_for_date(self, target: date) -> list[Reading]:
        return self.fixed_for_date(target) + self.movable_for_date(target)

    def next_sunday(self, today: Optional[date] = None) -> date:
        today = today or date.today()
        return sunday_on_or_after(today)

    def calculated_calendar(self, year: int) -> list[tuple[date, str, bool]]:
        items = []
        for day, titles in sorted(calculated_movables(year).items()):
            for title in titles:
                items.append((day, title, normalize_key(title) in self.movable_rows))
        return items


def format_reading(reading: Reading, target: date | None = None) -> str:
    date_part = f" — {target.strftime('%B %-d, %Y')}" if target else ""
    # Windows does not support %-d; fix later in bot if needed.
    lines = [f"**{reading.title}{date_part}**"]
    if reading.intent:
        lines.append(f"*{reading.intent}*")
    if reading.collect:
        lines.append(f"\n**Collect**\n{reading.collect}")
    if reading.reading_source or reading.reading:
        heading = f"**Reading"
        if reading.reading_source:
            heading += f": {reading.reading_source}"
        heading += "**"
        lines.append(f"\n{heading}\n{reading.reading}")
    if reading.gospel_source or reading.gospel:
        heading = f"**Gospel"
        if reading.gospel_source:
            heading += f": {reading.gospel_source}"
        heading += "**"
        lines.append(f"\n{heading}\n{reading.gospel}")
    if reading.notes:
        lines.append(f"\n**Notes**\n{reading.notes}")
    return "\n".join(lines)


def split_discord_message(text: str, limit: int = 1900) -> list[str]:
    """Split long readings into Discord-safe message chunks."""
    if len(text) <= limit:
        return [text]
    chunks = []
    current = ""
    for para in text.split("\n\n"):
        if len(current) + len(para) + 2 <= limit:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            if len(para) <= limit:
                current = para
            else:
                for i in range(0, len(para), limit):
                    chunks.append(para[i:i+limit])
                current = ""
    if current:
        chunks.append(current)
    return chunks
