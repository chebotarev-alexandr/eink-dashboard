# e-ink панель (Raspberry Pi Zero 2 W + Waveshare 2.13")

Настольная панель на e-ink экране. По кругу показывает экраны:

1. **Погода** — текущая температура, ощущается, ветер, мин/макс (Open-Meteo, без ключа).
2. **Серверы** — доступность твоих сервисов (HTTP-проверка).
3. **Сегодня** — события на сегодня из Remember_bot (твой бот напоминаний).
4. **Спутники** — ближайшие пролёты (МКС и любые другие по NORAD ID) над городом, по TLE.

## Железо

- Raspberry Pi Zero 2 W
- Waveshare 2.13" E-Ink HAT (250×122, ч/б)

## Установка на Raspberry Pi

```bash
# 1. Включить SPI: sudo raspi-config -> Interface Options -> SPI -> Enable
# 2. Системные пакеты
sudo apt update
sudo apt install -y python3-pip python3-pil fonts-dejavu

# 3. Зависимости проекта
pip install -r requirements.txt

# 4. Библиотека Waveshare (SPI/GPIO) — из официального репозитория
git clone https://github.com/waveshare/e-Paper
cp -r e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd .
# (также понадобятся spidev и RPi.GPIO — см. README репозитория e-Paper)
```

## Настройка

Всё в `config.py`: город/координаты, список серверов, спутники, ротация экранов.

Токен планировщика задай переменной окружения (не коммить в репозиторий):

```bash
export PLANNER_API_TOKEN=...
```

Важно: `EPD_MODEL` в `config.py` — версия платы (V4/V3/V2/2in13). Если картинка
«мусорная» или инвертированная — поменяй на другую.

## Запуск

```bash
# проверка логики (текст в консоль)
python main.py --mode console

# проверка отрисовки (сохраняет PNG в frames/)
python main.py --mode png --once

# вывод на e-ink
python main.py --mode eink
```

## Автозапуск (systemd)

```ini
# /etc/systemd/system/eink-dashboard.service
[Unit]
Description=E-ink dashboard
After=network.target

[Service]
WorkingDirectory=/home/pi/eink-dashboard
Environment=PLANNER_API_TOKEN=...
ExecStart=/usr/bin/python3 main.py --mode eink
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now eink-dashboard
```

## Структура

- `config.py` — настройки.
- `screens.py` — какой экран какие данные собирает.
- `providers/` — погода, серверы, события, спутники.
- `renderer.py` — отрисовка экранов (ConsoleRenderer / EinkRenderer).
- `display.py` — абстракция дисплея (e-ink / PNG-заглушка).
- `main.py` — цикл ротации.
