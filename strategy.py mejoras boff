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


# ================= ZONA HTF =================

def get_zone(df_htf):
    highs = df_htf["high"].rolling(20).max()
    lows = df_htf["low"].rolling(20).min()

    resistance = highs.iloc[-1]
    support = lows.iloc[-1]

    return support, resistance


# ================= TOQUE FLEXIBLE =================

def double_touch(df_m5, level, is_support=True):
    touches = 0

    for i in range(-10, 0):
        candle = df_m5.iloc[i]

        if is_support:
            if candle["low"] <= level:
                touches += 1
        else:
            if candle["high"] >= level:
                touches += 1

    # 🔥 antes era >= 2 (muy estricto)
    return touches >= 1


# ================= CONFIRMACIÓN MEJORADA =================

def confirmation(df_m1, direction):
    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]

    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    strong = body > (range_ * 0.5)

    if direction == "call":
        return last["close"] > last["open"] and strong and last["close"] > prev["close"]

    if direction == "put":
        return last["close"] < last["open"] and strong and last["close"] < prev["close"]

    return False


# ================= SEÑAL =================

def pro_signal(df_m1, df_m5, df_htf):

    if len(df_htf) < 20:
        return None, None

    support, resistance = get_zone(df_htf)

    price = df_m1["close"].iloc[-1]
    atr = df_m1["atr"].iloc[-1]

    if np.isnan(atr):
        return None, None

    # 🔥 buffer más flexible
    buffer = atr * 1.8

    # ========= SOPORTE =========

    if abs(price - support) <= buffer:
        if double_touch(df_m5, support, True):
            if confirmation(df_m1, "call"):

                # ⚡ entrada rápida si está muy cerca
                if abs(price - support) <= atr:
                    return "put", 1

    # ========= RESISTENCIA =========

    if abs(price - resistance) <= buffer:
        if double_touch(df_m5, resistance, False):
            if confirmation(df_m1, "put"):

                if abs(price - resistance) <= atr:
                    return "call", 1

    return None, None
