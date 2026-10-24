"""Точка входа: бесконечный цикл ротации экранов.

Режимы (--mode):
  console — текст в консоль (проверка логики, без железа и Pillow)
  png     — отрисовка в PNG-файлы в каталоге frames/ (проверка отрисовки)
  eink    — вывод на Waveshare 2.13" (требует SPI + библиотеку Waveshare)

Примеры:
  python main.py --mode console
  python main.py --mode png
  python main.py --mode eink
"""

import argparse
import signal
import time

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

    cache = {}  # screen_id -> (timestamp, data)
    running = True

    def _stop(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    print(f"Панель запущена ({args.mode}). Экраны: {[s['id'] for s in config.SCREENS]}")

    while running:
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

            try:
                renderer.render(data)
            except Exception as exc:  # noqa: BLE001
                print(f"[{sid}] ошибка отрисовки: {exc}")

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
