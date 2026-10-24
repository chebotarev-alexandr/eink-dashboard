"""Пролёты спутников над точкой (skyfield + TLE с запасными источниками).

TLE берём с celestrak, при сбое (блокировка/500) — с tle.ivanstanojevic.me
(любой NORAD id). Точное предсказание: время восхода, макс. высота, длительность.
"""

from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from . import http


def _fetch_tle(norad_id):
    # 1) celestrak — обычный текст
    try:
        url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"
        text = http.get_text(url, timeout=15, retries=1)
        lines = text.strip().splitlines()
        if len(lines) >= 3:
            return lines[0].strip(), lines[1].strip(), lines[2].strip()
    except Exception:
        pass

    # 2) запасной источник (JSON, любой NORAD id)
    data = http.get_json(f"https://tle.ivanstanojevic.me/api/tle/{norad_id}", timeout=15, retries=1)
    return data.get("name", "SAT"), data["line1"], data["line2"]


def next_passes(latitude, longitude, tz_name, satellites, count, ahead_days):
    """Ближайшие пролёты всех спутников, отсортированные по времени."""
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
