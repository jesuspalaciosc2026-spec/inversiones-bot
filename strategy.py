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


def too_far_from_ema(df):

    last = df.iloc[-1]
    ema = df["ema20"].iloc[-1]

    distance = abs(last["close"] - ema)
    avg_range = (df["high"] - df["low"]).mean()

    return distance > avg_range * 2


# ================= LIQUIDEZ =================

def liquidity_sweep(df):

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return True

    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return True

    return False


# ================= RECHAZO =================

def institutional_rejection(df):

    last = df.iloc[-1]

    upper = last["high"] - max(last["close"], last["open"])
    lower = min(last["close"], last["open"]) - last["low"]
    body = abs(last["close"] - last["open"])

    return upper > body * 2 or lower > body * 2


# ================= AGOTAMIENTO =================

def exhaustion(df):

    recent = df.tail(5)

    total_body = 0
    total_range = 0

    for i in range(len(recent)):
        candle = recent.iloc[i]
        total_body += abs(candle["close"] - candle["open"])
        total_range += candle["high"] - candle["low"]

    if total_range == 0:
        return False

    return (total_body / total_range) < 0.4


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


# ================= COMPRESIÓN =================

def compression_zone(df):

    recent = df.tail(5)

    total = 0
    for i in range(len(recent)):
        total += (recent.iloc[i]["high"] - recent.iloc[i]["low"])

    avg = total / 5
    overall = recent["high"].max() - recent["low"].min()

    return overall < avg * 2


# ================= RUPTURA =================

def breakout_candle(df, trend):

    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])
    full = last["high"] - last["low"]

    if full == 0:
        return False

    strength = body / full

    if trend == "call":
        return last["close"] > last["open"] and strength > 0.6

    if trend == "put":
        return last["close"] < last["open"] and strength > 0.6

    return False


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1):

    if df_m1 is None or len(df_m1) < 30:
        return None, None

    df = add_ema(df_m1.copy())

    score = 0

    # 1. tendencia
    trend, t_score = trend_strength(df)
    score += t_score

    if trend is None:
        return None, None

    # 2. filtros base
    if avoid_overextension(df):
        score += 10

    if not too_far_from_ema(df):
        score += 10

    if not liquidity_sweep(df):
        score += 10

    if not institutional_rejection(df):
        score += 10

    if not exhaustion(df):
        score += 10

    # 3. estructura
    if detect_pullback(df, trend):
        score += 15
    else:
        return None, None

    if weak_pullback(df):
        score += 15

    if near_ema(df):
        score += 10

    if continuation_candle(df, trend):
        score += 10
    else:
        return None, None

    # 🔥 TIMING PERFECTO
    if compression_zone(df):
        score += 10
    else:
        return None, None

    if breakout_candle(df, trend):
        score += 10
    else:
        return None, None

    # 🎯 DECISIÓN FINAL
    if score >= 80:
        print(f"🔥 ENTRY SNIPER | SCORE: {score}")
        return trend, 1

    print(f"❌ SCORE BAJO: {score}")
    return None, None
