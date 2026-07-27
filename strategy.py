import numpy as np

# ==============================
# 🔹 ATR
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
# 🔹 Tendencia
# ==============================
def get_trend(candles):
    closes = [c["close"] for c in candles]

    ma_fast = np.mean(closes[-5:])
    ma_slow = np.mean(closes[-15:])

    if ma_fast > ma_slow:
        return "call"
    elif ma_fast < ma_slow:
        return "put"
    return None


# ==============================
# 🔹 Lateral
# ==============================
def is_lateral(candles):
    highs = [c["max"] for c in candles[-10:]]
    lows = [c["min"] for c in candles[-10:]]

    rango = max(highs) - min(lows)

    return rango < 0.0004


# ==============================
# 🔥 SEÑAL INDIVIDUAL
# ==============================
def pro_signal(candles):
    if len(candles) < 20:
        return None, 0

    atr = calculate_atr(candles)
    if atr is None or atr < 0.0003:
        return None, 0

    if is_lateral(candles):
        return None, 0

    trend = get_trend(candles)
    if trend is None:
        return None, 0

    last = candles[-1]
    prev = candles[-2]

    fuerza = abs(last["close"] - prev["close"])

    # breakout limpio
    if trend == "call" and last["close"] > prev["max"]:
        return "call", fuerza

    if trend == "put" and last["close"] < prev["min"]:
        return "put", fuerza

    return None, 0


# ==============================
# 🚀 MULTI PAR PRO
# ==============================
def pro_signal_multi(market_data):

    best_pair = None
    best_signal = None
    best_strength = 0

    for pair, candles in market_data.items():
        signal, strength = pro_signal(candles)

        if signal and strength > best_strength:
            best_pair = pair
            best_signal = signal
            best_strength = strength

    if best_pair is None:
        return None, None, 0

    return best_pair, best_signal, best_strength
