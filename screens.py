"""Экраны панели: какой экран какие данные собирает."""

import config


def collect(screen_id):
    """Собирает данные экрана. Возвращает dict с ключом `type` и данными."""
    if screen_id == "clock_weather":
        from providers import network, weather

        return {
            "type": "clock_weather",
            "weather": weather.fetch(
                config.LATITUDE, config.LONGITUDE, config.PLANNER_API_TOKEN, config.WEATHER_URL
            ),
            "ip": network.get_ip(),
        }

    if screen_id == "servers":
        from providers import servers

        return {"type": "servers", "servers": servers.check_all(config.SERVERS)}

    if screen_id == "planner":
        from providers import planner

        data = planner.fetch(config.PLANNER_API_URL, config.PLANNER_API_TOKEN)
        events = planner.todays_events(data.get("events", []), data.get("timezone", config.TIMEZONE))
        return {"type": "planner", "timezone": data.get("timezone"), "events": events}

    if screen_id == "satellites":
        from providers import satellites

        return {
            "type": "satellites",
            "passes": satellites.next_passes(
                config.LATITUDE,
                config.LONGITUDE,
                config.TIMEZONE,
                config.SATELLITES,
                config.SATELLITES_PASS_COUNT,
                config.SATELLITES_AHEAD_DAYS,
            ),
        }

    if screen_id == "home":
        from providers import network, weather, planner

        w = weather.fetch(
            config.LATITUDE, config.LONGITUDE, config.PLANNER_API_TOKEN, config.WEATHER_URL
        )
        p = planner.fetch(config.PLANNER_API_URL, config.PLANNER_API_TOKEN)
        events = planner.todays_events(p.get("events", []), p.get("timezone", config.TIMEZONE))
        return {
            "type": "home",
            "weather": w,
            "ip": network.get_ip(),
            "events": events,
            "timezone": p.get("timezone", config.TIMEZONE),
        }

    raise ValueError(f"Неизвестный экран: {screen_id}")
