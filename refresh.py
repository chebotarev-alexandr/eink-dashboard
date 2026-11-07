"""Политика полного/частичного обновления e-ink при смене времени (домашний режим).

Полный рефреш (с очисткой от призраков) нужен, когда частичный оставил бы
видимые артефакты на цифрах. Два случая:

1. Изменилось больше одной цифры (напр. «14:19» -> «14:20» — единицы «9»->«0»,
   десятки «1»->«2»): частичный рефреш не перекроет все изменившиеся глифы.
2. В единственной изменившейся цифре погас «важный» сегмент — его призрак на
   новой цифре портит читаемость (напр. «5» с призраком верхне-правого сегмента
   «4» читается как «9»/«6»).
"""

# 7-сегментное представление цифр 0-9.
# a=верх, b=верх-право, c=низ-право, d=низ, e=низ-лево, f=верх-лево, g=середина.
SEGMENTS = {
    "0": "abcdef",
    "1": "bc",
    "2": "abged",
    "3": "abgcd",
    "4": "fgbc",
    "5": "afgcd",
    "6": "afgedc",
    "7": "abc",
    "8": "abcdefg",
    "9": "abcdfg",
}

# Сегменты, чей «призрак» реально ломает читаемость соседней цифры:
# горизонтали (верх/середина/низ) и верхне-правый вертикальный.
PROMINENT = {"a", "b", "d", "g"}


def _bad_transition(old_digit, new_digit):
    """True, если переход old_digit -> new_digit требует полного рефреша."""
    old = set(SEGMENTS.get(old_digit, ""))
    new = set(SEGMENTS.get(new_digit, ""))
    off = old - new  # сегменты, которые погаснут
    return len(off) >= 2 or bool(off & PROMINENT)


def needs_full_refresh(old_time, new_time):
    """True, если переход old_time -> new_time (формат «HH:MM») требует полного рефреша."""
    if not old_time:
        return True
    changed = 0
    bad = False
    for old_ch, new_ch in zip(old_time, new_time):
        if old_ch == new_ch:
            continue
        changed += 1
        if _bad_transition(old_ch, new_ch):
            bad = True
    return changed > 1 or bad
