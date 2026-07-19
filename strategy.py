import numpy as np

# ================= INDICADORES =================
def add_indicators(df):
    df = df.copy()
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift(1))
    low_close = abs(df["low"] - df["close"].shift(1))
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
    return touches >= 2  # Más seguridad en OTC

# ================= CONFIRMACIÓN MEJORADA =================
def confirmation(df_m1, direction):
    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]
    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]
    strong = body > (range_ * 0.5)

    if direction == "call":
        return (last["close"] > last["open"] and 
                strong and 
                last["close"] > prev["close"] and
                last["close"] == last["high"])  # Cierre en máximo = impulso total

    if direction == "put":
        return (last["close"] < last["open"] and 
                strong and 
                last["close"] < prev["close"] and
                last["close"] == last["low"])  # Cierre en mínimo = rechazo total
    return False

# ================= SEÑAL =================
def pro_signal(df_m1, df_m5, df_htf):
    if len(df_htf) < 20:
        return None, None
    support, resistance = get_zone(df_htf)
    price = df_m1["close"].iloc[-1]
    ema20 = df_m1["ema20"].iloc[-1]
    atr = df_m1["atr"].iloc[-1]
    if np.isnan(atr):
        return None, None

    buffer = atr * 1.3  # Más ajustado

    # ========= SOPORTE =========
    if abs(price - support) <= buffer:
        if price > ema20:  # A favor de tendencia alcista
            if double_touch(df_m5, support, True):
                if confirmation(df_m1, "call"):
                    return "call", 1

    # ========= RESISTENCIA =========
    if abs(price - resistance) <= buffer:
        if price < ema20:  # A favor de tendencia bajista
            if double_touch(df_m5, resistance, False):
                if confirmation(df_m1, "put"):
                    return "put", 1

    return None, None
