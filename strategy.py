import numpy as np

# ================= INDICADORES =================

def add_indicators(df):
    df = df.copy()

    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()

    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())

    df["tr"] = np.maximum(high_low, np.maximum(high_close, low_close))
    df["atr"] = df["tr"].rolling(14).mean()

    return df


# ================= ZONAS =================

def get_zone(df):
    resistance = df["high"].rolling(20).max().iloc[-1]
    support = df["low"].rolling(20).min().iloc[-1]
    return support, resistance


# ================= FILTROS =================

def is_lateral(df):
    atr = df["atr"].iloc[-1]
    high = df["high"].rolling(10).max().iloc[-1]
    low = df["low"].rolling(10).min().iloc[-1]

    return (high - low) < atr * 1.5


def strong_impulse(df):
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    atr = df["atr"].iloc[-1]

    return body > atr * 0.5


def far_from_ema(df):
    price = df["close"].iloc[-1]
    ema = df["ema20"].iloc[-1]
    atr = df["atr"].iloc[-1]

    return abs(price - ema) > atr * 0.7


def not_exhausted(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    body_last = abs(last["close"] - last["open"])
    body_prev = abs(prev["close"] - prev["open"])

    return body_last >= body_prev


def no_fake_breakout(df, support, resistance):
    last = df.iloc[-1]

    if last["high"] > resistance and last["close"] < resistance:
        return False

    if last["low"] < support and last["close"] > support:
        return False

    return True


def near_zone(price, support, resistance, atr):
    buffer = atr * 1.5

    if abs(price - support) <= buffer:
        return "support"

    if abs(price - resistance) <= buffer:
        return "resistance"

    return None


# ================= CORRELACIÓN EUR =================

def euro_strength(data):
    directions = []

    for pair in ["EURUSD", "EURGBP"]:
        df = data[pair][0]
        if df["close"].iloc[-1] > df["open"].iloc[-1]:
            directions.append("up")
        else:
            directions.append("down")

    if directions.count("up") >= 2:
        return "bullish"

    if directions.count("down") >= 2:
        return "bearish"

    return None


# ================= MEJOR PAR =================

def best_pair(data):
    best = None
    best_score = 0

    for pair, (df_m1, _, _) in data.items():
        body = abs(df_m1["close"].iloc[-1] - df_m1["open"].iloc[-1])
        atr = df_m1["atr"].iloc[-1]

        if atr == 0 or np.isnan(atr):
            continue

        score = body / atr

        if score > best_score:
            best_score = score
            best = pair

    return best


# ================= SEÑAL FINAL =================

def pro_signal_multi(data):

    # usar EURUSD como referencia
    df_ref = add_indicators(data["EURUSD"][0])

    if is_lateral(df_ref):
        return None, None, None

    if not strong_impulse(df_ref):
        return None, None, None

    if not far_from_ema(df_ref):
        return None, None, None

    if not not_exhausted(df_ref):
        return None, None, None

    eur = euro_strength(data)

    if eur is None:
        return None, None, None

    pair = best_pair(data)

    if pair is None:
        return None, None, None

    df_m1, _, df_htf = data[pair]

    df_m1 = add_indicators(df_m1)

    price = df_m1["close"].iloc[-1]
    atr = df_m1["atr"].iloc[-1]

    support, resistance = get_zone(df_htf)

    if not no_fake_breakout(df_m1, support, resistance):
        return None, None, None

    zone = near_zone(price, support, resistance, atr)

    if zone is None:
        return None, None, None

    last = df_m1.iloc[-1]

    # ================= ENTRADA FINAL =================

    if eur == "bullish" and last["close"] > last["open"]:
        return pair, "call", 1

    if eur == "bearish" and last["close"] < last["open"]:
        return pair, "put", 1

    return None, None, None
