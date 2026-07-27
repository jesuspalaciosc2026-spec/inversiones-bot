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


def euro_strength(data):
    up = 0
    down = 0

    for pair in ["EURUSD", "EURGBP"]:
        df = data[pair][0]

        if df["close"].iloc[-1] > df["open"].iloc[-1]:
            up += 1
        else:
            down += 1

    if up >= 2:
        return "bullish"

    if down >= 2:
        return "bearish"

    return None


def best_pair(data):
    best = None
    best_score = 0

    for pair, (df_m1, _, _) in data.items():
        body = abs(df_m1["close"].iloc[-1] - df_m1["open"].iloc[-1])
        atr = df_m1["atr"].iloc[-1]

        if np.isnan(atr) or atr == 0:
            continue

        score = body / atr

        if score > best_score:
            best_score = score
            best = pair

    return best


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal_multi(data):

    if "EURUSD" not in data or "EURGBP" not in data:
        return None, None, None

    df_ref = add_indicators(data["EURUSD"][0])

    # FILTROS FUERTES
    if is_lateral(df_ref):
        return None, None, None

    if not strong_impulse(df_ref):
        return None, None, None

    eur = euro_strength(data)

    if eur is None:
        return None, None, None

    pair = best_pair(data)

    if pair is None:
        return None, None, None

    df_m1 = add_indicators(data[pair][0])

    last = df_m1.iloc[-1]

    # ENTRADA FINAL
    if eur == "bullish" and last["close"] > last["open"]:
        return pair, "call", 1

    if eur == "bearish" and last["close"] < last["open"]:
        return pair, "put", 1

    return None, None, None


# ================= COMPATIBILIDAD (IMPORTANTE) =================
# Esto evita errores si aún llamas pro_signal en algún lado

def pro_signal(*args, **kwargs):
    return None, None
