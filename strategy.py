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
        return None

    atr = calculate_atr(candles)
    if atr is None or atr < 0.0003:
        return None

    if is_lateral(candles):
        return None

    trend = get_trend(candles)
    if trend is None:
        return None

    last = candles[-1]
    prev = candles[-2]

    # breakout limpio
    if trend == "call" and last["close"] > prev["max"]:
        return "call"

    if trend == "put" and last["close"] < prev["min"]:
        return "put"

    return None


# ==============================
# 🚀 MULTI PAR (TU ESTRATEGIA PRO)
# ==============================
def pro_signal_multi(market_data):
    """
    market_data = {
        "EURUSD": candles,
        "EURJPY": candles,
        "EURGBP": candles
    }
    """

    signals = {}

    for pair, candles in market_data.items():
        signal = pro_signal(candles)
        if signal:
            signals[pair] = signal

    if not signals:
        return None, None

    # 🔥 elegir el mejor (más limpio)
    best_pair = list(signals.keys())[0]
    best_signal = signals[best_pair]

    return best_pair, best_signal
