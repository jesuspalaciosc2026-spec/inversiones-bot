import numpy as np

# ================= UTILIDADES =================

def is_bullish(c):
    return c["close"] > c["open"]

def is_bearish(c):
    return c["close"] < c["open"]

def body_size(c):
    return abs(c["close"] - c["open"])

def candle_range(c):
    return c["high"] - c["low"]

def upper_wick(c):
    return c["high"] - max(c["close"], c["open"])

def lower_wick(c):
    return min(c["close"], c["open"]) - c["low"]


# ================= 1. DETECTAR TENDENCIA =================

def detect_trend(df):

    last = df.tail(5)

    bullish = sum(is_bullish(c) for _, c in last.iterrows())
    bearish = sum(is_bearish(c) for _, c in last.iterrows())

    if bullish >= 4:
        return "call"

    if bearish >= 4:
        return "put"

    return None


# ================= 2. DETECTAR RETROCESO =================

def detect_pullback(df, direction):

    candles = df.tail(3)

    if direction == "call":
        return all(is_bearish(c) for _, c in candles.iterrows())

    if direction == "put":
        return all(is_bullish(c) for _, c in candles.iterrows())

    return False


# ================= 3. INDECISIÓN =================

def detect_indecision(df):

    candles = df.tail(2)

    small = 0

    for _, c in candles.iterrows():
        if body_size(c) < candle_range(c) * 0.4:
            small += 1

    return small >= 1


# ================= 4. RECHAZO =================

def detect_rejection(df, direction):

    last = df.iloc[-1]

    if direction == "call":
        return lower_wick(last) > body_size(last)

    if direction == "put":
        return upper_wick(last) > body_size(last)

    return False


# ================= 5. CONTINUACIÓN =================

def confirmation(df, direction):

    last = df.iloc[-1]

    if direction == "call":
        return is_bullish(last)

    if direction == "put":
        return is_bearish(last)

    return False


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1, df_m5, df_htf):

    # usamos M1 directo (tu nueva lógica)
    df = df_m1

    # 1. Tendencia
    direction = detect_trend(df)
    if direction is None:
        return None, None

    # 2. Pullback
    if not detect_pullback(df.iloc[:-1], direction):
        return None, None

    # 3. Indecisión
    if not detect_indecision(df):
        return None, None

    # 4. Rechazo
    if not detect_rejection(df, direction):
        return None, None

    # 5. Confirmación
    if not confirmation(df, direction):
        return None, None

    # 6. Expiración fija 1 minuto
    return direction, 1
