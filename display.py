"""Абстракция дисплея: e-ink (Waveshare 2.13") или PNG-заглушка для отладки."""

import os

WIDTH, HEIGHT = 250, 122


class ImageDisplay:
    """Сохраняет кадры в PNG — чтобы проверить отрисовку без железа."""

    def __init__(self, out_dir="frames"):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self._n = 0

    def show(self, image):
        self._n += 1
        path = os.path.join(self.out_dir, f"frame_{self._n:04d}.png")
        image.save(path)
        return path


class EinkDisplay:
    """Waveshare 2.13" (250×122, ч/б). Драйвер подключается лениво.

    Требует включённый SPI и библиотеку Waveshare (см. README).
    model: "2in13", "2in13_V2", "2in13_V3", "2in13_V4" — подбирается под версию
    платы (V3/V4 — самые свежие, контроллер SSD1680).
    """

    _MODULES = {
        "2in13": "epd2in13",
        "2in13_V2": "epd2in13_V2",
        "2in13_V3": "epd2in13_V3",
        "2in13_V4": "epd2in13_V4",
    }

    def __init__(self, model="2in13_V4"):
        self.model = model
        self._epd = None

    def _load(self):
        if self._epd is not None:
            return self._epd
        import importlib

        name = self._MODULES.get(self.model)
        if not name:
            raise ValueError(f"Неизвестная модель e-ink: {self.model}")
        try:
            mod = importlib.import_module(f"waveshare_epd.{name}")
        except ImportError as exc:
            raise ImportError(
                f"Не найден драйвер waveshare_epd.{name}. "
                "Скопируйте lib/waveshare_epd из репозитория Waveshare e-Paper (см. README)."
            ) from exc
        self._epd = mod.EPD()
        self._epd.init()
        self._epd.Clear(0xFF)
        return self._epd

    def show(self, image):
        epd = self._load()
        epd.display(epd.getbuffer(image))

    def sleep(self):
        if self._epd is not None:
            self._epd.sleep()
