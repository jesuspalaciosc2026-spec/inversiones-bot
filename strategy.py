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


# ================= FILTROS =================

def is_sideways(df):
    recent = df.tail(10)
    highs = recent["high"]
    lows = recent["low"]

    rango = highs.max() - lows.min()
    velas = (highs - lows).mean()

    return rango < velas * 2


def is_explosive(c):
    body = body_size(c)
    rango = candle_range(c)
    return body > rango * 0.8


def avoid_fake_move(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    return abs(last["close"] - prev["close"]) < (last["high"] - last["low"]) * 1.5


# ================= TENDENCIA =================

def detect_trend(df):
    last = df.tail(5)

    bullish = sum(is_bullish(c) for _, c in last.iterrows())
    bearish = sum(is_bearish(c) for _, c in last.iterrows())

    if bullish >= 4:
        return "call"
    if bearish >= 4:
        return "put"

    return None


# ================= PULLBACK =================

def detect_pullback(df, direction):

    candles = df.tail(3)

    sizes = [body_size(c) for _, c in candles.iterrows()]

    if direction == "call":
        return all(is_bearish(c) for _, c in candles.iterrows()) and max(sizes) < np.mean(sizes) * 1.5

    if direction == "put":
        return all(is_bullish(c) for _, c in candles.iterrows()) and max(sizes) < np.mean(sizes) * 1.5

    return False


# ================= INDECISIÓN =================

def detect_indecision(df):

    candles = df.tail(2)

    small = 0

    for _, c in candles.iterrows():
        if body_size(c) < candle_range(c) * 0.4:
            small += 1

    return small >= 1


# ================= RECHAZO =================

def detect_rejection(df, direction):

    last = df.iloc[-1]

    if direction == "call":
        return lower_wick(last) > body_size(last)

    if direction == "put":
        return upper_wick(last) > body_size(last)

    return False


# ================= CONFIRMACIÓN =================

def strong_confirmation(df, direction):

    last = df.iloc[-1]

    body = body_size(last)
    rango = candle_range(last)

    fuerza = body / rango if rango > 0 else 0

    if direction == "call":
        return last["close"] > last["open"] and fuerza > 0.6

    if direction == "put":
        return last["close"] < last["open"] and fuerza > 0.6

    return False


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1, df_m5=None, df_htf=None):

    df = df_m1

    if len(df) < 10:
        return None, None

    # ❌ filtro lateral
    if is_sideways(df):
        return None, None

    # ❌ vela explosiva
    if is_explosive(df.iloc[-1]):
        return None, None

    # ❌ fake move
    if not avoid_fake_move(df):
        return None, None

    # ✅ tendencia
    direction = detect_trend(df)
    if direction is None:
        return None, None

    # ✅ pullback
    if not detect_pullback(df.iloc[:-1], direction):
        return None, None

    # ✅ indecisión
    if not detect_indecision(df):
        return None, None

    # ✅ rechazo
    if not detect_rejection(df, direction):
        return None, None

    # ✅ confirmación fuerte
    if not strong_confirmation(df, direction):
        return None, None

    return direction, 1
