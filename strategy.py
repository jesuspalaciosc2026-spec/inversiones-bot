import numpy as np

# ================= INDICADORES =================
def add_indicators(df):
    df = df.copy()

    # EMA 20 corregido
    df["ema20"] = df["close"].ewm(span=20, adjust=False, min_periods=20).mean()

    # ATR 14 corregido
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift(1))
    low_close = abs(df["low"] - df["close"].shift(1))
    df["tr"] = np.maximum(high_low, np.maximum(high_close, low_close))
    df["atr"] = df["tr"].rolling(window=14, min_periods=14).mean()

    return df


# ================= ZONA HTF =================
def get_zone(df_htf):
    highs = df_htf["high"].rolling(window=20, min_periods=15).max()
    lows = df_htf["low"].rolling(window=20, min_periods=15).min()
    resistance = highs.iloc[-1]
    support = lows.iloc[-1]
    return support, resistance


# ================= DOBLE TEST =================
def double_touch(df_m5, level, is_support=True):
    touches = 0
    # Revisamos solo velas cerradas, sin la última en formación
    for i in range(-11, -1):
        candle = df_m5.iloc[i]
        if is_support:
            if candle["low"] <= level and candle["close"] > level:
                touches += 1
        else:
            if candle["high"] >= level and candle["close"] < level:
                touches += 1
    return touches >= 2


# ================= CONFIRMACIÓN =================
def confirmation(df_m1, direction, level):
    actual = df_m1.iloc[-1]
    anterior = df_m1.iloc[-2]

    if direction == "call":
        return (actual["close"] > actual["open"]
                and actual["close"] > anterior["close"]
                and actual["close"] > level
                and (actual["close"] - actual["open"]) > (actual["atr"] * 0.3))

    if direction == "put":
        return (actual["close"] < actual["open"]
                and actual["close"] < anterior["close"]
                and actual["close"] < level
                and (actual["open"] - actual["close"]) > (actual["atr"] * 0.3))

    return False


# ================= SEÑAL FINAL (CORREGIDO) =================
def pro_signal(df_m1, df_m5, df_htf):
    # Validación mínima de datos
    if len(df_htf) < 20 or len(df_m5) < 15 or len(df_m1) < 10:
        return None, None  # ✅ Devuelve EXACTAMENTE 2 valores

    if "atr" not in df_m1.columns:
        df_m1 = add_indicators(df_m1)

    support, resistance = get_zone(df_htf)
    price = df_m1["close"].iloc[-1]
    atr = df_m1["atr"].iloc[-1]

    if np.isnan(atr) or atr <= 0:
        return None, None  # ✅ Siempre 2 valores

    buffer = atr * 0.8

    # SEÑAL CALL (EXPIRACIÓN 1 MINUTO)
    if abs(price - support) <= buffer:
        if double_touch(df_m5, support, True):
            if confirmation(df_m1, "call", support):
                return "call", 1  # ✅ 2 valores: dirección, expiración

    # SEÑAL PUT (EXPIRACIÓN 1 MINUTO)
    if abs(price - resistance) <= buffer:
        if double_touch(df_m5, resistance, False):
            if confirmation(df_m1, "put", resistance):
                return "put", 1  # ✅ 2 valores: dirección, expiración

    return None, None  # ✅ Nunca falla al desempaquetar
