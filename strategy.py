import numpy as np

# ==============================
# 🔹 ATR (volatilidad real)
# ==============================
def calculate_atr(candles, period=14):
    trs = []

    for i in range(1, len(candles)):
        high = candles[i]["max"]
        low = candles[i]["min"]
        prev_close = candles[i - 1]["close"]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        trs.append(tr)

    if len(trs) < period:
        return None

    return sum(trs[-period:]) / period


# ==============================
# 🔹 Tendencia simple
# ==============================
def get_trend(candles):
    closes = [c["close"] for c in candles]

    ma_fast = np.mean(closes[-5:])
    ma_slow = np.mean(closes[-15:])

    if ma_fast > ma_slow:
        return "up"
    elif ma_fast < ma_slow:
        return "down"
    return None


# ==============================
# 🔹 Lateral (evitar operar)
# ==============================
def is_lateral(candles):
    highs = [c["max"] for c in candles[-10:]]
    lows = [c["min"] for c in candles[-10:]]

    rango = max(highs) - min(lows)

    return rango < 0.0004  # mercado muerto


# ==============================
# 🔥 FUNCIÓN PRINCIPAL (PRO)
# ==============================
def pro_signal(candles):
    if len(candles) < 20:
        return None

    atr = calculate_atr(candles)
    if atr is None:
        return None

    # ❌ evitar mercado sin movimiento
    if atr < 0.0003:
        return None

    # ❌ evitar lateral
    if is_lateral(candles):
        return None

    trend = get_trend(candles)
    if trend is None:
        return None

    last = candles[-1]
    prev = candles[-2]

    # ==============================
    # 🚀 BREAKOUT REAL (tu enfoque)
    # ==============================
    if trend == "up":
        if last["close"] > prev["max"]:
            return "call"

    if trend == "down":
        if last["close"] < prev["min"]:
            return "put"

    return None
