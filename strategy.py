import numpy as np

# ================= DIVIDIR FASES =================

def split_phases(df_5s):

    ticks = df_5s.tail(12)

    return {
        "p1": ticks.iloc[0:3],
        "p2": ticks.iloc[3:6],
        "p3": ticks.iloc[6:9],
        "p4": ticks.iloc[9:12]
    }


# ================= MOVIMIENTO =================

def movement(df):

    return df["close"].iloc[-1] - df["open"].iloc[0]


# ================= VELOCIDAD =================

def speed(df):

    moves = []

    for i in range(1, len(df)):
        diff = abs(df.iloc[i]["close"] - df.iloc[i-1]["close"])
        moves.append(diff)

    return np.mean(moves) if moves else 0


# ================= DOMINANCIA =================

def dominance(df):

    buyers = 0
    sellers = 0

    for i in range(len(df)):
        if df.iloc[i]["close"] > df.iloc[i]["open"]:
            buyers += 1
        else:
            sellers += 1

    return buyers, sellers


# ================= ZONA DE VALOR =================

def value_zone(df_5s):

    closes = df_5s["close"].values
    return np.mean(closes)


# ================= ANÁLISIS COMPLETO =================

def analyze_candle(df_5s):

    phases = split_phases(df_5s)

    m1 = movement(phases["p1"])
    m2 = movement(phases["p2"])
    m3 = movement(phases["p3"])
    m4 = movement(phases["p4"])

    s1 = speed(phases["p1"])
    s4 = speed(phases["p4"])

    buyers, sellers = dominance(df_5s)

    open_price = df_5s.iloc[-12]["open"]
    close_price = df_5s.iloc[-1]["close"]

    total_move = close_price - open_price

    value = value_zone(df_5s)

    return {
        "m1": m1,
        "m2": m2,
        "m3": m3,
        "m4": m4,
        "s1": s1,
        "s4": s4,
        "buyers": buyers,
        "sellers": sellers,
        "total": total_move,
        "value": value,
        "close": close_price
    }


# ================= DECISIÓN =================

def pro_signal(df_m1, df_5s):

    if df_5s is None or len(df_5s) < 20:
        return None, None

    data = analyze_candle(df_5s)

    # ================= CONTINUACIÓN FUERTE =================
    if (
        data["total"] > 0 and
        data["buyers"] > data["sellers"] and
        data["m4"] > data["m1"] and  # más fuerza al final
        data["s4"] > data["s1"]      # aceleración final
    ):
        return "call", 1

    if (
        data["total"] < 0 and
        data["sellers"] > data["buyers"] and
        data["m4"] < data["m1"] and
        data["s4"] > data["s1"]
    ):
        return "put", 1

    # ================= MANIPULACIÓN =================
    if data["m1"] > 0 and data["m4"] < 0:
        return "put", 1

    if data["m1"] < 0 and data["m4"] > 0:
        return "call", 1

    # ================= ABSORCIÓN =================
    if data["total"] < 0 and data["buyers"] > data["sellers"]:
        return "call", 1

    if data["total"] > 0 and data["sellers"] > data["buyers"]:
        return "put", 1

    return None, None
