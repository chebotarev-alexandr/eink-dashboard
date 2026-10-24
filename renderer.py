"""Рендер экранов.

Сейчас только ConsoleRenderer — печатает данные в консоль, чтобы прогнать
логику без экрана. Когда будет известна модель e-ink модуля, сюда добавится
EinkRenderer (принимает те же dict-данные и рисует изображение).
"""


class Renderer:
    def render(self, data: dict) -> None:
        raise NotImplementedError


class ConsoleRenderer(Renderer):
    """Текстовая заглушка для проверки логики сбора и ротации."""

    def render(self, data):
        t = data["type"]
        print(f"\n=== {t} ===")
        if t == "clock_weather":
            w = data["weather"]
            print(f"{w['icon']} {w['weather']}, {w['temp']}°C (ощущается {w['feels_like']}°C)")
            print(f"Макс {w['high']}° / мин {w['low']}° · влажность {w['humidity']}% · ветер {w['wind']} м/с")
        elif t == "servers":
            for s in data["servers"]:
                status = "OK  " if s["ok"] else "FAIL"
                detail = f"{s['latency_ms']} мс" if s.get("latency_ms") is not None else (s.get("error") or "—")
                print(f"  [{status}] {s['name']} — {detail}")
        elif t == "planner":
            if not data["events"]:
                print("  На сегодня ничего не запланировано")
            for e in data["events"]:
                print(f"  {e['time']} · {e['text']}")
        elif t == "satellites":
            if not data["passes"]:
                print("  Нет ближайших пролётов")
            for p in data["passes"]:
                print(f"  🛰 {p['name']}: {p['time']} · макс {p['max_elevation']}° · ~{p['duration_min']} мин")
        else:
            print("  (нет отрисовки для этого типа)")
