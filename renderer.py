"""Рендер экранов.

- ConsoleRenderer — текст в консоль (для быстрой проверки логики).
- EinkRenderer   — рисует кадр 250×122 (Waveshare 2.13" ч/б) через Pillow и
                   отдаёт его объекту Display (e-ink или PNG-заглушка).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 250, 122
MARGIN = 8
CONTENT_Y = 28
ROW_H = 22

# Кириллические шрифты по умолчанию (на Raspberry Pi OS ставятся пакетом fonts-dejavu)
DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DEFAULT_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


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


class EinkRenderer(Renderer):
    """Рисует экраны в ч/б 250×122 и отдаёт кадр объекту Display."""

    def __init__(self, display, font_path=DEFAULT_FONT, font_path_bold=DEFAULT_FONT_BOLD, timezone="Asia/Vladivostok"):
        self.display = display
        self.font_path = font_path
        self.font_path_bold = font_path_bold
        self.timezone = ZoneInfo(timezone)
        self._fonts = {}

    # ------------------------------------------------------------- fonts
    def _font(self, size, bold=False):
        key = (size, bold)
        if key not in self._fonts:
            path = self.font_path_bold if bold else self.font_path
            try:
                self._fonts[key] = ImageFont.truetype(path, size)
            except OSError:
                # fallback: системный шрифт PIL (без кириллицы — только для отладки)
                self._fonts[key] = ImageFont.load_default()
        return self._fonts[key]

    def _truncate(self, text, font, max_w):
        if font.getlength(text) <= max_w:
            return text
        while text and font.getlength(text + "…") > max_w:
            text = text[:-1]
        return text + "…"

    def _base(self, title):
        img = Image.new("1", (WIDTH, HEIGHT), 255)
        d = ImageDraw.Draw(img)
        now = datetime.now(self.timezone).strftime("%H:%M")
        tf = self._font(13, bold=True)
        cf = self._font(12)
        d.text((MARGIN, 4), title, font=tf, fill=0)
        d.text((WIDTH - MARGIN - cf.getlength(now), 5), now, font=cf, fill=0)
        d.line([(MARGIN, 22), (WIDTH - MARGIN, 22)], fill=0, width=1)
        return img, d

    # ------------------------------------------------------------- screens
    def draw(self, data):
        t = data["type"]
        if t == "clock_weather":
            return self._draw_clock_weather(data)
        if t == "servers":
            return self._draw_servers(data)
        if t == "planner":
            return self._draw_planner(data)
        if t == "satellites":
            return self._draw_satellites(data)
        raise ValueError(f"Неизвестный тип экрана: {t}")

    def render(self, data):
        self.display.show(self.draw(data))

    def _draw_clock_weather(self, data):
        w = data["weather"]
        img, d = self._base("Хабаровск")
        big = self._font(34, bold=True)
        body = self._font(12)
        small = self._font(11)

        temp = f"{w['temp']}°"
        d.text((MARGIN, CONTENT_Y - 2), temp, font=big, fill=0)
        d.text((MARGIN + big.getlength(temp) + 10, CONTENT_Y + 8), w["weather"], font=body, fill=0)

        d.text((MARGIN, 74), f"Ощущается {w['feels_like']}°  ·  ветер {w['wind']} м/с", font=small, fill=0)
        d.text((MARGIN, 92), f"Макс {w['high']}° / мин {w['low']}°  ·  влажность {w['humidity']}%", font=small, fill=0)
        return img

    def _draw_servers(self, data):
        img, d = self._base("Серверы")
        body = self._font(12)
        y = CONTENT_Y
        for s in data["servers"]:
            mark = "✓" if s["ok"] else "✗"
            detail = f"{s['latency_ms']} мс" if s.get("latency_ms") is not None else (s.get("error") or "—")
            name = self._truncate(s["name"], body, WIDTH - 2 * MARGIN - 70)
            d.text((MARGIN, y), mark, font=body, fill=0)
            d.text((MARGIN + 16, y), name, font=body, fill=0)
            d.text((WIDTH - MARGIN - body.getlength(detail), y), detail, font=body, fill=0)
            y += ROW_H
        return img

    def _draw_planner(self, data):
        img, d = self._base("Сегодня")
        body = self._font(12)
        y = CONTENT_Y
        if not data["events"]:
            d.text((MARGIN, y), "На сегодня пусто", font=body, fill=0)
            return img
        for e in data["events"]:
            text = self._truncate(e["text"], body, WIDTH - 2 * MARGIN - 52)
            d.text((MARGIN, y), e["time"], font=body, fill=0)
            d.text((MARGIN + 50, y), text, font=body, fill=0)
            y += ROW_H
        return img

    def _draw_satellites(self, data):
        img, d = self._base("Спутники")
        body = self._font(12)
        y = CONTENT_Y
        if not data["passes"]:
            d.text((MARGIN, y), "Нет ближайших пролётов", font=body, fill=0)
            return img
        for p in data["passes"]:
            line = f"{p['name']}  {p['time']}  ↑{p['max_elevation']}°  {p['duration_min']} мин"
            d.text((MARGIN, y), self._truncate(line, body, WIDTH - 2 * MARGIN), font=body, fill=0)
            y += ROW_H
        return img
