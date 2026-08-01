import pandas as pd

# =========================================================
# 🧼 NORMALIZAR DATA
# =========================================================
def fix_df(df):

    if "max" in df.columns:
        df["high"] = df["max"]

    if "min" in df.columns:
        df["low"] = df["min"]

    required = ["open", "close", "high", "low"]

    for col in required:
        if col not in df.columns:
            return None

    return df


# =========================================================
# 🧠 ANALISIS DE VELA (DOMINANCIA REAL)
# =========================================================
def analyze_candle(c):

    body = abs(c["close"] - c["open"])
    range_total = c["high"] - c["low"]

    if range_total == 0:
        return None, 0

    strength = body / range_total

    # Dominancia
    if c["close"] > c["open"]:
        direction = "call"
    else:
        direction = "put"

    return direction, strength


# =========================================================
# 🚫 DETECTAR ZONAS DE REVERSIÓN (60 velas)
# =========================================================
def near_reversal_zone(df):

    recent = df.tail(60)

    highs = recent["high"]
    lows = recent["low"]

    resistance = highs.max()
    support = lows.min()

    price = df.iloc[-1]["close"]

    # muy cerca de extremos
    if abs(price - resistance) < 0.0002:
        return True

    if abs(price - support) < 0.0002:
        return True

    return False


# =========================================================
# 🚫 DETECTAR FINAL DE IMPULSO
# =========================================================
def is_late_move(df):

    count = 0

    for i in range(-2, -10, -1):
        if df.iloc[i]["close"] > df.iloc[i]["open"]:
            count += 1
        else:
            break

    if count >= 4:
        return True

    count = 0

    for i in range(-2, -10, -1):
        if df.iloc[i]["close"] < df.iloc[i]["open"]:
            count += 1
        else:
            break

    if count >= 4:
        return True

    return False


# =========================================================
# 🎯 SCORE
# =========================================================
def build_score(strength):

    score = 0

    # fuerza de la vela
    if strength > 0.6:
        score += 40
    elif strength > 0.5:
        score += 30
    elif strength > 0.4:
        score += 20

    return score


# =========================================================
# 🚀 PRO SIGNAL (NUEVA LÓGICA)
# =========================================================
def pro_signal(df_m1, df_m5):

    df_m1 = fix_df(df_m1)

    if df_m1 is None:
        return None, None, None

    if len(df_m1) < 60:
        return None, None, None

    last = df_m1.iloc[-1]

    # =============================
    # ANALISIS DE VELA
    # =============================
    direction, strength = analyze_candle(last)

    if direction is None:
        return None, None, None

    # =============================
    # SOLO CONTINUIDAD
    # =============================
    if strength < 0.5:
        return None, None, None

    # =============================
    # EVITAR REVERSIÓN
    # =============================
    if near_reversal_zone(df_m1):
        return None, None, None

    # =============================
    # EVITAR FINAL DE IMPULSO
    # =============================
    if is_late_move(df_m1):
        return None, None, None

    # =============================
    # SCORE
    # =============================
    score = build_score(strength)

    if score < 20:
        return None, None, None

    return direction, score, "continuation"


# =========================================================
# 🧠 RESULTADOS
# =========================================================
stats = {
    "wins": 0,
    "loss": 0
}

def update_result(result, pattern):

    global stats

    if result == 1:
        stats["wins"] += 1
    else:
        stats["loss"] += 1

    print(f"📊 {pattern} → W:{stats['wins']} L:{stats['loss']}")
