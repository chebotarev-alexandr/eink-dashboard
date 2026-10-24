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
    {"name": "Чат-мост", "url": "http://132.243.115.71:9091/health"},
    {"name": "Vaultwarden", "url": "https://vaultwarden-personal.space"},
]

# Планировщик: события владельца из Remember_bot
PLANNER_API_URL = "http://132.243.115.71:8091/api/my-events/"
# Токен задай через переменную окружения (не коммить в репозиторий):
#   export PLANNER_API_TOKEN=...
PLANNER_API_TOKEN = os.environ.get("PLANNER_API_TOKEN", "")

# Спутники: чьи пролёты показывать (NORAD id) и сколько ближайших
SATELLITES = [
    {"name": "МКС", "norad_id": 25544},
]
SATELLITES_PASS_COUNT = 3
SATELLITES_AHEAD_DAYS = 2

# Ротация экранов: (id, сколько секунд показывать, как часто обновлять данные в секундах)
SCREENS = [
    {"id": "clock_weather", "title": "Погода", "duration": 60, "refresh": 1800},
    {"id": "servers", "title": "Серверы", "duration": 45, "refresh": 300},
    {"id": "planner", "title": "Сегодня", "duration": 60, "refresh": 300},
    {"id": "satellites", "title": "Спутники", "duration": 45, "refresh": 21600},
]
