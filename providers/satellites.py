"""Пролёты спутников над точкой (skyfield + TLE с celestrak, без ключей).

Точное предсказание по TLE: время восхода, максимальная высота над горизонтом
и длительность пролёта. Работает для любого спутника по NORAD ID.
"""

import urllib.request
from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo


def _fetch_tle(norad_id):
    url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"
    req = urllib.request.Request(url, headers={"User-Agent": "eink-dashboard"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8")
    lines = text.strip().splitlines()
    if len(lines) < 3:
        raise ValueError(f"Пустой TLE для NORAD {norad_id}")
    return lines[0].strip(), lines[1].strip(), lines[2].strip()


def next_passes(latitude, longitude, tz_name, satellites, count, ahead_days):
    """Ближайшие пролёты всех спутников, отсортированные по времени.

    satellites: [{"name": "МКС", "norad_id": 25544}, ...]
    """
    from skyfield.api import EarthSatellite, load, wgs84

    ts = load.timescale()
    loc = wgs84.latlon(latitude, longitude)
    tz = ZoneInfo(tz_name)

    t0 = ts.now()
    t1 = ts.utc(datetime.now(dt_timezone.utc) + timedelta(days=ahead_days))

    passes = []
    for s in satellites:
        sat_name, line1, line2 = _fetch_tle(s["norad_id"])
        sat = EarthSatellite(line1, line2, sat_name, ts)
        t, events = sat.find_events(loc, t0, t1, altitude_degrees=0.0)

        i = 0
        while i + 2 < len(events):
            # 0 = восход, 1 = кульминация (макс. высота), 2 = заход
            if events[i] == 0 and events[i + 1] == 1 and events[i + 2] == 2:
                rise = t[i].astimezone(tz)
                alt, _, _ = (sat - loc).at(t[i + 1]).altaz()
                duration_min = round((t[i + 2].tt - t[i].tt) * 24 * 60)
                passes.append({
                    "name": s.get("name", sat_name),
                    "time": rise.strftime("%d.%m %H:%M"),
                    "max_elevation": int(round(alt.degrees)),
                    "duration_min": max(1, duration_min),
                })
                i += 3
            else:
                i += 1

    passes.sort(key=lambda p: p["time"])
    return passes[:count]
