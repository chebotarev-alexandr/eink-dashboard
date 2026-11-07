"""Точка входа: цикл ротации экранов + веб-морда.

Режимы (--mode):
  console — текст в консоль (проверка логики, без железа и Pillow)
  png     — отрисовка в PNG-файлы в каталоге frames/ (проверка отрисовки)
  eink    — вывод на Waveshare 2.13" (требует SPI + библиотеку Waveshare)

Домашний режим (config.HOME_MODE = True): один экран (погода + время + планы),
время обновляется частичным рефрешем (без чёрной вспышки); полный рефреш — только
при смене >1 цифры или «плохом» переходе (см. refresh.py).

Веб-морда поднимается всегда, если config.WEB_ENABLED = True:
  http://<ip>:8080  — страница;  /api/data — JSON со всеми данными.
"""

import argparse
import signal
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import config
from screens import collect


def main():
    parser = argparse.ArgumentParser(description="E-ink панель")
    parser.add_argument("--mode", choices=["console", "png", "eink"], default="console")
    parser.add_argument("--once", action="store_true", help="Один проход всех экранов и выход")
    args = parser.parse_args()

    if args.mode == "console":
        from renderer import ConsoleRenderer

        renderer = ConsoleRenderer()
    else:
        from renderer import EinkRenderer

        if args.mode == "png":
            from display import ImageDisplay

            display = ImageDisplay()
        else:
            from display import EinkDisplay

            display = EinkDisplay(model=config.EPD_MODEL)

        renderer = EinkRenderer(display, timezone=config.TIMEZONE)

    cache = {}     # screen_id -> (timestamp, data)
    snapshot = {}  # screen_id -> data (для веб-морды)

    def collect_screen(screen):
        sid = screen["id"]
        cached = cache.get(sid)
        now = time.time()
        if cached is not None and now - cached[0] < screen["refresh"]:
            return cached[1]
        try:
            data = collect(sid)
            cache[sid] = (now, data)
        except Exception as exc:  # noqa: BLE001 — не роняем цикл
            print(f"[{sid}] ошибка сбора данных: {exc}")
            data = cached[1] if cached else {"type": sid, "error": str(exc)}
        return data

    # Веб-морда
    web_server = None
    if getattr(config, "WEB_ENABLED", False) and not args.once:
        from web import start_web_server

        web_server = start_web_server(lambda: snapshot, host=config.WEB_HOST, port=config.WEB_PORT)
        print(f"Веб-морда: http://<ip>:{config.WEB_PORT}")

    # Прогрев: собрать всё сразу, чтобы веб-морда была полной с первой секунды
    for screen in config.SCREENS:
        snapshot[screen["id"]] = collect_screen(screen)

    running = True

    def _stop(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    # ------------------------------------------------------ Домашний режим
    if getattr(config, "HOME_MODE", False):
        from refresh import needs_full_refresh

        home = {"id": "home", "refresh": getattr(config, "HOME_DATA_REFRESH_SEC", 600)}
        last_time = ""
        print(f"Домашний режим: время каждые {config.TIME_REFRESH_SEC}с; "
              f"полный рефреш — при смене >1 цифры или «плохом» переходе")
        while running:
            data = collect_screen(home)
            snapshot["home"] = data
            now_str = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%H:%M")
            try:
                if needs_full_refresh(last_time, now_str) or args.once:
                    renderer.render(data)
                else:
                    renderer.render_partial(data)
            except Exception as exc:  # noqa: BLE001
                print(f"[home] ошибка отрисовки: {exc}")
            last_time = now_str
            if args.once:
                break
            time.sleep(config.TIME_REFRESH_SEC)

        display = getattr(renderer, "display", None)
        if display is not None and hasattr(display, "sleep"):
            display.sleep()
        print("Панель остановлена.")
        return

    # ------------------------------------------------------ Ротация экранов
    print(f"Панель запущена ({args.mode}). Экраны: {[s['id'] for s in config.SCREENS]}")

    while running:
        for screen in config.SCREENS:
            data = collect_screen(screen)
            snapshot[screen["id"]] = data
            try:
                renderer.render(data)
            except Exception as exc:  # noqa: BLE001
                print(f"[{screen['id']}] ошибка отрисовки: {exc}")
            if args.once:
                continue
            time.sleep(screen["duration"])

        if args.once:
            break

    display = getattr(renderer, "display", None)
    if display is not None and hasattr(display, "sleep"):
        display.sleep()
    print("Панель остановлена.")


if __name__ == "__main__":
    main()
