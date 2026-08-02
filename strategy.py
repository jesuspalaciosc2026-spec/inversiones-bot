import pandas as pd

# =========================
# 🔍 LATERALIDAD
# =========================
def is_lateral(df):
    last = df.tail(20)
    rango = last["high"].max() - last["low"].min()
    return rango < 0.002


# =========================
# 💥 RUPTURA LATERAL
# =========================
def ruptura_lateral(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    cuerpo = abs(last["close"] - last["open"])
    rango = last["high"] - last["low"]

    if cuerpo > rango * 0.6:
        if last["close"] > prev["high"]:
            return "call"
        elif last["close"] < prev["low"]:
            return "put"

    return None


# =========================
# 📉 ZONA QUEMADA
# =========================
def zona_repetida(df):
    precio = df["close"].iloc[-1]
    rep = 0

    for i in range(-15, -1):
        if abs(df["close"].iloc[i] - precio) < 0.0003:
            rep += 1

    return rep >= 3


# =========================
# 🕯 VELA LIMPIA
# =========================
def vela_limpia(df):
    last = df.iloc[-1]

    cuerpo = abs(last["close"] - last["open"])
    upper = last["high"] - max(last["open"], last["close"])
    lower = min(last["open"], last["close"]) - last["low"]

    if upper > cuerpo:
        return False

    if lower > cuerpo:
        return False

    return True


# =========================
# 📈 CONTINUIDAD
# =========================
def continuidad(df, direccion):
    c1 = df.iloc[-2]
    c2 = df.iloc[-3]

    if direccion == "call":
        return c1["close"] > c1["open"] or c2["close"] > c2["open"]

    if direccion == "put":
        return c1["close"] < c1["open"] or c2["close"] < c2["open"]

    return False


# =========================
# 🔻 TENDENCIA BAJISTA
# =========================
def tendencia_bajista(df):
    highs = df["high"].tail(5).values
    lows = df["low"].tail(5).values

    return highs[0] > highs[-1] and lows[0] > lows[-1]


# =========================
# 🔺 TENDENCIA ALCISTA
# =========================
def tendencia_alcista(df):
    highs = df["high"].tail(5).values
    lows = df["low"].tail(5).values

    return highs[0] < highs[-1] and lows[0] < lows[-1]


# =========================
# 🔄 PULLBACK
# =========================
def pullback_alcista(df):
    velas = df.tail(4)
    verdes = sum(1 for _, v in velas.iterrows() if v["close"] > v["open"])
    return verdes >= 2


def pullback_bajista(df):
    velas = df.tail(4)
    rojas = sum(1 for _, v in velas.iterrows() if v["close"] < v["open"])
    return rojas >= 2


# =========================
# 💥 VELAS FUERTES
# =========================
def vela_fuerte_bajista(df):
    last = df.iloc[-1]
    cuerpo = abs(last["close"] - last["open"])
    rango = last["high"] - last["low"]

    return last["close"] < last["open"] and cuerpo > rango * 0.6


def vela_fuerte_alcista(df):
    last = df.iloc[-1]
    cuerpo = abs(last["close"] - last["open"])
    rango = last["high"] - last["low"]

    return last["close"] > last["open"] and cuerpo > rango * 0.6


# =========================
# 🔥 SETUP CONTINUACIÓN PUT
# =========================
def setup_continuacion_put(df):

    if not tendencia_bajista(df):
        return None

    if not pullback_alcista(df):
        return None

    if not vela_fuerte_bajista(df):
        return None

    return {
        "direction": "put",
        "score": 4
    }


# =========================
# 🔥 SETUP CONTINUACIÓN CALL
# =========================
def setup_continuacion_call(df):

    if not tendencia_alcista(df):
        return None

    if not pullback_bajista(df):
        return None

    if not vela_fuerte_alcista(df):
        return None

    return {
        "direction": "call",
        "score": 4
    }


# =========================
# ⭐ SCORE GENERAL
# =========================
def score_calidad(df, direccion):
    score = 0
    last = df.iloc[-1]

    cuerpo = abs(last["close"] - last["open"])
    rango = last["high"] - last["low"]

    if cuerpo > rango * 0.6:
        score += 2

    if continuidad(df, direccion):
        score += 2

    if vela_limpia(df):
        score += 1

    if zona_repetida(df):
        score -= 2

    return score


# =========================
# 🚀 FUNCIÓN PRINCIPAL
# =========================
def generate_signal(df):

    try:
        if len(df) < 30:
            return None

        # =========================
        # 🔥 PRIORIDAD: CONTINUACIÓN
        # =========================
        cont_put = setup_continuacion_put(df)
        if cont_put:
            return cont_put

        cont_call = setup_continuacion_call(df)
        if cont_call:
            return cont_call

        # =========================
        # 🔵 LATERAL + RUPTURA
        # =========================
        if not is_lateral(df):
            return None

        direccion = ruptura_lateral(df)
        if not direccion:
            return None

        if not continuidad(df, direccion):
            return None

        if zona_repetida(df):
            return None

        score = score_calidad(df, direccion)

        if score < 3:
            return None

        return {
            "direction": direccion,
            "score": score
        }

    except Exception as e:
        print("Error en estrategia:", e)
        return None
