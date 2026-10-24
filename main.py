"""Точка входа: бесконечный цикл ротации экранов.

Сейчас данные выводятся в консоль (ConsoleRenderer). Позже рендерер меняем
на e-ink — остальная логика (сбор, кэш, ротация) не меняется.

Запуск:  python main.py
"""

import time

import config
from renderer import ConsoleRenderer
from screens import collect


def main():
    renderer = ConsoleRenderer()
    cache = {}  # screen_id -> (timestamp, data)

    print(f"Панель запущена. Экраны: {[s['id'] for s in config.SCREENS]}")

    while True:
        for screen in config.SCREENS:
            sid = screen["id"]
            cached = cache.get(sid)
            now = time.time()

            if cached is None or now - cached[0] >= screen["refresh"]:
                try:
                    data = collect(sid)
                    cache[sid] = (now, data)
                except Exception as exc:  # noqa: BLE001 — не роняем цикл
                    print(f"[{sid}] ошибка сбора данных: {exc}")
                    data = cached[1] if cached else {"type": sid, "error": str(exc)}
            else:
                data = cached[1]

            renderer.render(data)
            time.sleep(screen["duration"])


if __name__ == "__main__":
    main()
