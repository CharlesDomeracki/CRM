import json
import re
import urllib.error
import urllib.request
from datetime import datetime

DAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]
DAY_ABBR_MAP = {
    "Mo": "Monday", "Tu": "Tuesday", "We": "Wednesday", "Th": "Thursday",
    "Fr": "Friday", "Sa": "Saturday", "Su": "Sunday",
}
DAY_ORDER = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

FIELD_BY_DAY = {
    "Monday": "monday_hours",
    "Tuesday": "tuesday_hours",
    "Wednesday": "wednesday_hours",
    "Thursday": "thursday_hours",
    "Friday": "friday_hours",
    "Saturday": "saturday_hours",
    "Sunday": "sunday_hours",
}


def _format_time(raw):
    raw = raw.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(raw, fmt).strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue
    return raw


def _normalize_day(value):
    value = value.strip()
    if "schema.org/" in value:
        value = value.rsplit("/", 1)[-1]
    value = value.capitalize()
    return value if value in DAY_NAMES else None


def _expand_day_range(token):
    if token in DAY_ORDER:
        return [token]
    if "-" in token:
        start, end = (part.strip() for part in token.split("-", 1))
        if start in DAY_ORDER and end in DAY_ORDER:
            i, j = DAY_ORDER.index(start), DAY_ORDER.index(end)
            if i <= j:
                return DAY_ORDER[i : j + 1]
    return []


def _parse_simple_opening_hours(values):
    hours = {}
    for entry in values:
        if not isinstance(entry, str) or " " not in entry.strip():
            continue
        days_part, time_part = entry.strip().split(" ", 1)
        if "-" not in time_part:
            continue
        open_raw, close_raw = time_part.split("-", 1)
        formatted = f"{_format_time(open_raw)} - {_format_time(close_raw)}"
        for token in days_part.split(","):
            for abbr in _expand_day_range(token.strip()):
                hours[DAY_ABBR_MAP[abbr]] = formatted
    return hours


def _parse_opening_hours_specification(specs):
    hours = {}
    for spec in specs:
        if not isinstance(spec, dict):
            continue
        days = spec.get("dayOfWeek")
        if isinstance(days, str):
            days = [days]
        elif not isinstance(days, list):
            continue
        opens, closes = spec.get("opens"), spec.get("closes")
        if not opens or not closes:
            continue
        formatted = f"{_format_time(opens)} - {_format_time(closes)}"
        for day in days:
            if not isinstance(day, str):
                continue
            day_name = _normalize_day(day)
            if day_name:
                hours[day_name] = formatted
    return hours


def _extract_hours_from_html(html):
    hours = {}
    pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    for match in re.finditer(pattern, html, re.S | re.I):
        try:
            data = json.loads(match.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            continue

        candidates = data if isinstance(data, list) else [data]
        objects = []
        for candidate in candidates:
            if isinstance(candidate, dict) and isinstance(candidate.get("@graph"), list):
                objects.extend(candidate["@graph"])
            else:
                objects.append(candidate)

        for obj in objects:
            if not isinstance(obj, dict):
                continue
            spec = obj.get("openingHoursSpecification")
            if spec:
                if isinstance(spec, dict):
                    spec = [spec]
                if isinstance(spec, list):
                    hours.update(_parse_opening_hours_specification(spec))
            simple = obj.get("openingHours")
            if simple:
                if isinstance(simple, str):
                    simple = [simple]
                if isinstance(simple, list):
                    hours.update(_parse_simple_opening_hours(simple))
    return hours


def fetch_hours_from_url(url, timeout=6):
    if not url:
        return {}
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; LeadsCRM/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            html = resp.read(500_000).decode(charset, errors="ignore")
    except (urllib.error.URLError, ValueError, OSError):
        return {}
    return _extract_hours_from_html(html)
