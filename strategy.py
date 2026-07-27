import numpy as np

# ==============================
# 🔹 ATR (ROBUSTO)
# ==============================
def calculate_atr(candles, period=14):
    if len(candles) < period + 1:
        return None

    trs = []

    for i in range(1, len(candles)):
        try:
            high = candles[i]["max"]
            low = candles[i]["min"]
            prev_close = candles[i - 1]["close"]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            trs.append(tr)
        except:
            return None

    if len(trs) < period:
        return None

    return sum(trs[-period:]) / period


# ==============================
# 🔹 TENDENCIA (MEJORADA)
# ==============================
def get_trend(candles):
    if len(candles) < 20:
        return None

    closes = [c["close"] for c in candles]

    ma_fast = np.mean(closes[-5:])
    ma_slow = np.mean(closes[-15:])

    # filtro de inclinación real
    if ma_fast > ma_slow and closes[-1] > closes[-5]:
        return "call"

    elif ma_fast < ma_slow and closes[-1] < closes[-5]:
        return "put"

    return None


# ==============================
# 🔹 MERCADO LATERAL (MEJORADO)
# ==============================
def is_lateral(candles):
    if len(candles) < 15:
        return True

    highs = [c["max"] for c in candles[-10:]]
    lows = [c["min"] for c in candles[-10:]]

    rango = max(highs) - min(lows)

    # filtro dinámico
    atr = calculate_atr(candles)
    if atr is None:
        return True

    return rango < atr * 1.2


# ==============================
# 🔹 IMPULSO REAL (NUEVO)
# ==============================
def strong_candle(candle):
    cuerpo = abs(candle["close"] - candle["open"])
    rango = candle["max"] - candle["min"]

    if rango == 0:
        return False

    fuerza = cuerpo / rango
    return fuerza > 0.6


# ==============================
# 🔥 SEÑAL INDIVIDUAL PRO
# ==============================
def pro_signal(candles):
    if len(candles) < 20:
        return None

    atr = calculate_atr(candles)

    # ❌ sin volatilidad real
    if atr is None or atr < 0.00025:
        return None

    # ❌ lateral
    if is_lateral(candles):
        return None

    trend = get_trend(candles)

    if trend is None:
        return None

    last = candles[-1]
    prev = candles[-2]

    # ❌ evitar velas débiles
    if not strong_candle(last):
        return None

    # 🔥 breakout limpio + impulso
    if trend == "call" and last["close"] > prev["max"]:
        return "call"

    if trend == "put" and last["close"] < prev["min"]:
        return "put"

    return None


# ==============================
# 🚀 MULTI PAR PRO REAL
# ==============================
def pro_signal_multi(market_data):
    mejores = []

    for pair, candles in market_data.items():
        try:
            signal = pro_signal(candles)

            if signal:
                atr = calculate_atr(candles)
                if atr:
                    mejores.append((pair, signal, atr))

        except Exception as e:
            print(f"Error en {pair}: {e}")

    # ❌ no hay señales
    if not mejores:
        return None, None

    # 🔥 elegir el mejor (más volatilidad = mejor oportunidad)
    mejores.sort(key=lambda x: x[2], reverse=True)

    best_pair, best_signal, _ = mejores[0]

    return best_pair, best_signal
