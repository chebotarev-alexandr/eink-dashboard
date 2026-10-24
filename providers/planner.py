"""События владельца из Remember_bot (/api/my-events/) + выборка «на сегодня»."""

import json
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo


def fetch(api_url, token):
    url = api_url + "?" + urllib.parse.urlencode({"token": token})
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def todays_events(events, timezone, now=None):
    """Оставляет события, актуальные на сегодня, и сортирует по времени.

    Возвращает список dict: {"time": "HH:MM", "text": str, "kind": str}.
    """
    tz = ZoneInfo(timezone)
    now = now or datetime.now(tz)
    today = now.date()

    result = []
    for e in events:
        kind = e.get("kind")
        text = e.get("text", "")

        if kind == "once":
            if e.get("remind_at"):
                dt = datetime.fromisoformat(e["remind_at"]).astimezone(tz)
                if dt.date() == today:
                    result.append((dt.strftime("%H:%M"), text, "once"))
        elif kind == "daily":
            if e.get("time"):
                result.append((e["time"], text, "daily"))
        elif kind == "weekly":
            if today.weekday() in (e.get("weekdays") or []) and e.get("time"):
                result.append((e["time"], text, "weekly"))
        elif kind == "monthly":
            if today.day == e.get("day_of_month") and e.get("time"):
                result.append((e["time"], text, "monthly"))

    result.sort(key=lambda x: x[0])  # "HH:MM" сортируется как время
    return [{"time": t, "text": txt, "kind": k} for t, txt, k in result]
