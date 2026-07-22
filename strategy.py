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


# ================= TOQUE FLEXIBLE (SOPORTE INTACTO) =================
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
    return touches >= 1


# ================= RECHAZO EN M5 (SOLO RESISTENCIA) =================
def rejection_resistance_m5(df_m5, resistance):
    rechazos = 0
    tolerancia = resistance * 1.0015
    for i in range(-8, 0):
        c = df_m5.iloc[i]
        if c["high"] >= resistance:
            if c["close"] < tolerancia and c["close"] < c["open"]:
                rechazos += 1
    return rechazos >= 1


# ================= CONFIRMACIÓN DIFERENCIADA =================
def confirmation(df_m1, direction, resistance=None):
    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]
    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    # 🟢 SOPORTE / CALL: LÓGICA ORIGINAL SIN CAMBIOS
    if direction == "call":
        strong = body > (range_ * 0.5)
        return last["close"] > last["open"] and strong and last["close"] > prev["close"]

    # 🔴 RESISTENCIA / PUT: CONDICIONES MEJORADAS
    if direction == "put":
        cuerpo_fuerte = body > (range_ * 0.6)
        cierre_cerca_minimo = (last["high"] - last["close"]) > (range_ * 0.7)
        continuacion = last["close"] < prev["close"]
        sin_ruptura = last["high"] < (resistance * 1.002) if resistance is not None else True
        return last["close"] < last["open"] and cuerpo_fuerte and cierre_cerca_minimo and continuacion and sin_ruptura

    return False


# ================= SEÑAL FINAL =================
def pro_signal(df_m1, df_m5, df_htf):
    if len(df_htf) < 20:
        return None, None

    support, resistance = get_zone(df_htf)
    price = df_m1["close"].iloc[-1]
    atr = df_m1["atr"].iloc[-1]

    if np.isnan(atr):
        return None, None

    buffer = atr * 1.8

    # ========= SOPORTE =========
    if abs(price - support) <= buffer:
        if double_touch(df_m5, support, True):
            if confirmation(df_m1, "call"):
                expi = 2 if abs(price - support) <= atr else 3
                return "call", expi

    # ========= RESISTENCIA (MEJORADA) =========
    if abs(price - resistance) <= buffer:
        if rejection_resistance_m5(df_m5, resistance):
            if confirmation(df_m1, "put", resistance):
                expi = 2 if abs(price - resistance) <= atr else 3
                return "put", expi

    return None, None
