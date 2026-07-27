import numpy as np

# ================= INDICADORES =================

def add_indicators(df):
    df = df.copy()

    # EMA 20
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()

    # ATR 14
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())

    df["tr"] = np.maximum(high_low, np.maximum(high_close, low_close))
    df["atr"] = df["tr"].rolling(14).mean()

    return df


# ================= ZONAS =================

def get_zone(df_htf):
    resistance = df_htf["high"].rolling(20).max().iloc[-1]
    support = df_htf["low"].rolling(20).min().iloc[-1]
    return support, resistance


# ================= FILTRO LATERAL =================

def is_lateral(df):
    atr = df["atr"].iloc[-1]

    rango = df["high"].rolling(10).max().iloc[-1] - df["low"].rolling(10).min().iloc[-1]

    return rango < atr * 1.2


# ================= FUERZA TENDENCIA =================

def strong_trend(df):
    price = df["close"].iloc[-1]
    ema = df["ema20"].iloc[-1]
    atr = df["atr"].iloc[-1]

    return abs(price - ema) > atr * 0.5


# ================= DOBLE TOQUE =================

def double_touch(df, level, atr, is_support=True):
    touches = 0

    for i in range(-10, 0):
        candle = df.iloc[i]

        if is_support:
            if abs(candle["low"] - level) <= atr:
                touches += 1
        else:
            if abs(candle["high"] - level) <= atr:
                touches += 1

    return touches >= 2


# ================= HORARIO PRO =================

def is_good_session():
    import datetime
    hour = datetime.datetime.utcnow().hour

    # Londres + NY
    return 7 <= hour <= 16


# ================= SEÑAL PRO =================

def pro_signal(df_m1, df_m5, df_htf):

    # VALIDACIÓN DATOS
    if len(df_m1) < 20 or len(df_m5) < 20 or len(df_htf) < 20:
        return None, None

    df_m1 = add_indicators(df_m1)
    df_m5 = add_indicators(df_m5)

    # FILTRO HORARIO
    if not is_good_session():
        return None, None

    # FILTRO LATERAL
    if is_lateral(df_m1):
        return None, None

    # FILTRO TENDENCIA
    if not strong_trend(df_m1):
        return None, None

    support, resistance = get_zone(df_htf)

    price = df_m1["close"].iloc[-1]
    atr = df_m1["atr"].iloc[-1]

    if np.isnan(atr):
        return None, None

    buffer = atr * 1.2

    ema = df_m1["ema20"].iloc[-1]
    trend_up = price > ema
    trend_down = price < ema

    last = df_m1.iloc[-1]
    body = abs(last["close"] - last["open"])

    # =====================================================
    # 🟩 CONTINUIDAD (PRIORIDAD)
    # =====================================================

    if price > resistance + buffer and trend_up:
        if last["close"] > last["open"] and body > atr * 0.4:
            return "call", 1

    if price < support - buffer and trend_down:
        if last["close"] < last["open"] and body > atr * 0.4:
            return "put", 1

    # =====================================================
    # 🟥 REVERSIÓN (SOLO SI ES MUY CLARA)
    # =====================================================

    upper_wick = last["high"] - max(last["open"], last["close"])
    lower_wick = min(last["open"], last["close"]) - last["low"]

    # SOPORTE
    if abs(price - support) <= buffer:
        if lower_wick > body * 1.5 and not trend_down:
            if double_touch(df_m5, support, atr, True):
                return "call", 1

    # RESISTENCIA
    if abs(price - resistance) <= buffer:
        if upper_wick > body * 1.5 and not trend_up:
            if double_touch(df_m5, resistance, atr, False):
                return "put", 1

    return None, None
