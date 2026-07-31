import numpy as np

# ================= EMA =================

def add_ema(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    return df


# ================= TENDENCIA =================

def trend_strength(df):

    ema = df["ema20"]

    if ema.iloc[-1] < ema.iloc[-2]:
        return "put", 20

    if ema.iloc[-1] > ema.iloc[-2]:
        return "call", 20

    return None, 0


# ================= SOBREEXTENSIÓN =================

def avoid_overextension(df):

    recent = df.tail(4)
    strong = 0

    for i in range(len(recent)):
        body = abs(recent.iloc[i]["close"] - recent.iloc[i]["open"])
        full = recent.iloc[i]["high"] - recent.iloc[i]["low"]

        if full == 0:
            continue

        if (body / full) > 0.7:
            strong += 1

    return strong < 3


# ================= DISTANCIA EMA =================

def near_ema(df):

    last = df.iloc[-1]
    ema = df["ema20"].iloc[-1]

    distance = abs(last["close"] - ema)
    avg_range = (df["high"] - df["low"]).mean()

    return distance < avg_range


# ================= LIQUIDEZ =================

def liquidity_sweep(df):

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return True

    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return True

    return False


# ================= PULLBACK =================

def detect_pullback(df, trend):

    c1 = df.iloc[-1]
    c2 = df.iloc[-2]

    if trend == "put":
        return c1["close"] > c1["open"] and c2["close"] > c2["open"]

    if trend == "call":
        return c1["close"] < c1["open"] and c2["close"] < c2["open"]

    return False


# ================= PULLBACK DÉBIL =================

def weak_pullback(df):

    recent = df.tail(4)

    strength_sum = 0
    count = 0

    for i in range(len(recent)):
        candle = recent.iloc[i]

        body = abs(candle["close"] - candle["open"])
        full = candle["high"] - candle["low"]

        if full == 0:
            continue

        strength_sum += (body / full)
        count += 1

    if count == 0:
        return False

    return (strength_sum / count) < 0.5


# ================= CONFIRMACIÓN =================

def continuation_candle(df, trend):

    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])
    full = last["high"] - last["low"]

    if full == 0:
        return False

    strength = body / full

    if trend == "put":
        return last["close"] < last["open"] and strength > 0.5

    if trend == "call":
        return last["close"] > last["open"] and strength > 0.5

    return False


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1):

    if df_m1 is None or len(df_m1) < 30:
        return None, None

    df = add_ema(df_m1.copy())

    score = 0

    # 1. tendencia
    trend, trend_score = trend_strength(df)
    score += trend_score

    if trend is None:
        return None, None

    # 2. evitar sobreextensión
    if avoid_overextension(df):
        score += 10

    # 3. cerca EMA
    if near_ema(df):
        score += 15

    # 4. evitar trampa
    if not liquidity_sweep(df):
        score += 10

    # 5. pullback
    if detect_pullback(df, trend):
        score += 15
    else:
        return None, None

    # 6. pullback débil
    if weak_pullback(df):
        score += 20

    # 7. confirmación
    if continuation_candle(df, trend):
        score += 20
    else:
        return None, None

    # 🔥 DECISIÓN FINAL
    if score >= 80:
        print(f"✅ SCORE: {score}")
        return trend, 1

    print(f"❌ SCORE BAJO: {score}")
    return None, None
