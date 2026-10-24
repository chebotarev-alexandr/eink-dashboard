"""Настройки e-ink панели — правь под себя.

Никаких внешних зависимостей: только стандартная библиотека Python 3.9+.
"""

import os

# Местоположение и часовой пояс
CITY = "Хабаровск"
LATITUDE = 48.48
LONGITUDE = 135.07
TIMEZONE = "Asia/Vladivostok"

# Сервисы для экрана «Серверы» (имя + URL, проверяем GET-запросом)
SERVERS = [
    {"name": "Сайт code-orbit", "url": "https://code-orbit.ru"},
    {"name": "Бот напоминаний", "url": "http://132.243.115.71:8091/admin/"},
    {"name": "Vaultwarden", "url": "https://vaultwarden-personal.space"},
]

# Планировщик: события владельца из Remember_bot
PLANNER_API_URL = "http://132.243.115.71:8091/api/my-events/"
# Погода: проксируется через Remember_bot (open-meteo из РФ блокируется напрямую)
WEATHER_URL = "http://132.243.115.71:8091/api/weather/"
# Токен задай через переменную окружения (не коммить в репозиторий):
#   export PLANNER_API_TOKEN=...
PLANNER_API_TOKEN = os.environ.get("PLANNER_API_TOKEN", "")

# Спутники: чьи пролёты показывать (NORAD id) и сколько ближайших
SATELLITES = [
    {"name": "МКС", "norad_id": 25544},
]
SATELLITES_PASS_COUNT = 3
SATELLITES_AHEAD_DAYS = 2

# E-ink дисплей: Waveshare 2.13" (250×122, ч/б).
# Версия платы — если картинка «мусорная»/инвертированная, смени на другую.
EPD_MODEL = "2in13_V4"  # 2in13 / 2in13_V2 / 2in13_V3 / 2in13_V4

# Ротация экранов: (id, сколько секунд показывать, как часто обновлять данные в секундах)
SCREENS = [
    {"id": "clock_weather", "title": "Погода", "duration": 60, "refresh": 1800},
    {"id": "servers", "title": "Серверы", "duration": 45, "refresh": 300},
    {"id": "planner", "title": "Сегодня", "duration": 60, "refresh": 300},
    {"id": "satellites", "title": "Спутники", "duration": 45, "refresh": 21600},
]
