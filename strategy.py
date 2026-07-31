import numpy as np

# ================= TENDENCIA =================

def get_trend(df):

    closes = df["close"].values[-10:]

    up = 0
    down = 0

    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            up += 1
        elif closes[i] < closes[i-1]:
            down += 1

    if up > down:
        return "call"
    elif down > up:
        return "put"
    else:
        return None


# ================= PULLBACK =================

def detect_pullback(df):

    closes = df["close"].values

    # últimas 3 velas contra la tendencia
    c1, c2, c3 = closes[-1], closes[-2], closes[-3]

    if c1 < c2 < c3:
        return "bearish_pullback"

    if c1 > c2 > c3:
        return "bullish_pullback"

    return None


# ================= FUERZA =================

def strong_candle(df):

    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])
    full = last["high"] - last["low"]

    if full == 0:
        return False

    strength = body / full

    return strength > 0.6


# ================= EVITAR RANGO =================

def is_not_range(df):

    recent = df.tail(15)

    high = recent["high"].max()
    low = recent["low"].min()

    avg = (recent["high"] - recent["low"]).mean()

    return (high - low) > avg * 2


# ================= DIRECCIÓN FINAL =================

def hybrid_logic(df):

    trend = get_trend(df)

    if trend is None:
        return None

    pullback = detect_pullback(df)

    # 🔥 CONTINUACIÓN (TU PATRÓN)
    if trend == "call" and pullback == "bearish_pullback":
        if strong_candle(df):
            return "call"

    if trend == "put" and pullback == "bullish_pullback":
        if strong_candle(df):
            return "put"

    # 🔁 fallback (para no quedarse sin operar)
    return trend


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1):

    if df_m1 is None or len(df_m1) < 20:
        return None, None

    # filtro de rango
    if not is_not_range(df_m1):
        # aún así devuelve algo para no congelar el bot
        trend = get_trend(df_m1)
        if trend:
            return trend, 1
        return None, None

    direction = hybrid_logic(df_m1)

    if direction:
        return direction, 1

    return None, None
