"""IP-адрес машины (чтобы заходить по SSH)."""

import socket


def get_ip():
    """Локальный IP. Возвращает None, если сети нет."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # UDP-connect без реального трафика — лишь маршрут
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None
