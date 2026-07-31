import numpy as np

# ================= EMA =================

def add_ema(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    return df


# ================= DETECTAR TENDENCIA =================

def trend_direction(df):

    ema = df["ema20"]

    # pendiente de EMA
    if ema.iloc[-1] < ema.iloc[-2]:
        return "put"

    if ema.iloc[-1] > ema.iloc[-2]:
        return "call"

    return None


# ================= PULLBACK =================

def detect_pullback(df, trend):

    c1 = df.iloc[-1]
    c2 = df.iloc[-2]
    c3 = df.iloc[-3]

    # bajista → velas verdes (retroceso)
    if trend == "put":
        if c1["close"] > c1["open"] and c2["close"] > c2["open"]:
            return True

    # alcista → velas rojas (retroceso)
    if trend == "call":
        if c1["close"] < c1["open"] and c2["close"] < c2["open"]:
            return True

    return False


# ================= PULLBACK DÉBIL =================

def weak_pullback(df, trend):

    recent = df.tail(4)

    strength_sum = 0
    count = 0

    for i in range(len(recent)):
        candle = recent.iloc[i]

        body = abs(candle["close"] - candle["open"])
        full = candle["high"] - candle["low"]

        if full == 0:
            continue

        strength = body / full
        strength_sum += strength
        count += 1

    if count == 0:
        return False

    avg_strength = strength_sum / count

    # 🔥 clave: retroceso débil = poco cuerpo
    return avg_strength < 0.5


# ================= CERCA DE EMA =================

def near_ema(df):

    last = df.iloc[-1]
    ema = df["ema20"].iloc[-1]

    distance = abs(last["close"] - ema)

    avg_range = (df["high"] - df["low"]).mean()

    return distance < avg_range


# ================= CONFIRMACIÓN =================

def continuation_candle(df, trend):

    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])
    full = last["high"] - last["low"]

    if full == 0:
        return False

    strength = body / full

    # vela fuerte a favor de la tendencia
    if trend == "put":
        return last["close"] < last["open"] and strength > 0.5

    if trend == "call":
        return last["close"] > last["open"] and strength > 0.5

    return False


# ================= FILTRO ANTI MALAS ENTRADAS =================

def avoid_bad_entries(df):

    recent = df.tail(5)

    # ❌ evitar sobre-extensión (velas muy fuertes seguidas)
    big = 0

    for i in range(len(recent)):
        body = abs(recent.iloc[i]["close"] - recent.iloc[i]["open"])
        full = recent.iloc[i]["high"] - recent.iloc[i]["low"]

        if full == 0:
            continue

        if (body / full) > 0.7:
            big += 1

    if big >= 3:
        return False

    # ❌ evitar rango
    high = recent["high"].max()
    low = recent["low"].min()

    avg_range = (recent["high"] - recent["low"]).mean()

    if (high - low) < avg_range:
        return False

    return True


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1):

    if df_m1 is None or len(df_m1) < 30:
        return None, None

    df = add_ema(df_m1.copy())

    # 1. tendencia
    trend = trend_direction(df)
    if trend is None:
        return None, None

    # 2. evitar entradas malas
    if not avoid_bad_entries(df):
        return None, None

    # 3. pullback
    if not detect_pullback(df, trend):
        return None, None

    # 4. pullback débil
    if not weak_pullback(df, trend):
        return None, None

    # 5. cerca de EMA
    if not near_ema(df):
        return None, None

    # 6. confirmación (continuación)
    if not continuation_candle(df, trend):
        return None, None

    # ✅ ENTRADA PERFECTA
    return trend, 1
