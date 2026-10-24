"""Общий HTTP-клиент с повторами — для медленных/нестабильных сетей (РФ)."""

import json
import time
import urllib.request

USER_AGENT = "eink-dashboard"


def _get_bytes(url, timeout, retries):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise last_exc


def get_json(url, timeout=15, retries=2):
    return json.loads(_get_bytes(url, timeout, retries).decode("utf-8"))


def get_text(url, timeout=15, retries=2):
    return _get_bytes(url, timeout, retries).decode("utf-8")
