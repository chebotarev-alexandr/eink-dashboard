#!/usr/bin/env python3
"""Независимый монитор доступности серверов (для Raspberry Pi).

Каждый запуск (по cron раз в минуту) проверяет HTTP-доступность серверов.
При смене статуса (упал / снова поднялся) шлёт сообщение в Telegram.
Только стандартная библиотека Python — как и e-ink панель.

Настройка (переменные окружения или файл .env рядом со скриптом):
  MONITOR_BOT_TOKEN  — токен Telegram-бота (создай через @BotFather)
  MONITOR_CHAT_ID    — твой chat_id (куда слать алерты)

Серверы задаются списком SERVERS ниже.

Запуск:
  python3 uptime_monitor.py            # обычный прогон
  python3 uptime_monitor.py --dry-run  # только вывод в консоль, без Telegram
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

SERVERS = [
    {"name": "Амстердам (Vaultwarden/Hermes)", "url": "https://vaultwarden-personal.space"},
    {"name": "Сайт code-orbit", "url": "https://code-orbit.ru"},
    {"name": "Бот напоминаний", "url": "http://132.243.115.71:8091/admin/"},
]

TIMEOUT = 10
STATE_FILE = os.environ.get(
    "MONITOR_STATE_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".monitor_state.json"),
)


def _env_file():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def check(url):
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "uptime-monitor/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status < 500  # 4xx = сервер отвечает (жив), 5xx = проблема
    except Exception:
        return False


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)


def send_telegram(text):
    token = os.environ.get("MONITOR_BOT_TOKEN", "")
    chat_id = os.environ.get("MONITOR_CHAT_ID", "")
    if not token or not chat_id:
        print("нет MONITOR_BOT_TOKEN / MONITOR_CHAT_ID — пропускаю отправку")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10):
            return True
    except Exception as exc:
        print(f"не удалось отправить в Telegram: {exc}")
        return False


def main():
    _env_file()
    dry = "--dry-run" in sys.argv
    prev = load_state()
    new_state = {}
    messages = []
    statuses = []
    for s in SERVERS:
        ok = check(s["url"])
        new_state[s["name"]] = ok
        statuses.append(f"{s['name'].split(' ')[0]}={'OK' if ok else 'FAIL'}")
        prev_ok = prev.get(s["name"])
        if prev_ok is None:
            continue  # первый запуск — не спамим, просто запоминаем статус
        if ok and not prev_ok:
            messages.append(f"✅ {s['name']} снова доступен")
        elif not ok and prev_ok:
            messages.append(f"🔴 {s['name']} НЕДОСТУПЕН\n{s['url']}")

    if messages:
        text = "\n\n".join(messages)
        if dry:
            print("[dry-run] отправил бы:\n" + text)
        else:
            send_telegram(text)

    save_state(new_state)
    print("проверено: " + " · ".join(statuses))


if __name__ == "__main__":
    main()
