"""Проверка доступности сервисов (HTTP GET)."""

import time
import urllib.request

USER_AGENT = "eink-dashboard"


def check(url, timeout=8):
    started = time.time()
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
        return {"ok": status < 500, "status": status, "latency_ms": round((time.time() - started) * 1000)}
    except Exception as exc:  # noqa: BLE001 — любой сбой = «недоступен»
        return {"ok": False, "status": None, "error": str(exc)[:80]}


def check_all(servers):
    return [{"name": s["name"], **check(s["url"])} for s in servers]
