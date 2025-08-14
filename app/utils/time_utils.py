from __future__ import annotations

def round_minutes(value: int, mode: str, increment: int) -> int:
    if increment <= 0 or mode == "none":
        return max(1, value)
    inc = max(1, int(increment))
    q, r = divmod(value, inc)
    if r == 0:
        return value
    if mode == "down":
        return max(1, q * inc)
    if mode == "up":
        return (q + 1) * inc
    # nearest
    return (q + (1 if r >= inc / 2 else 0)) * inc


