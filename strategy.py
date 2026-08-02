import pandas as pd


# =========================
# 🔍 DETECCIÓN DE LATERALIDAD
# =========================
def is_lateral(df):
    last = df.tail(20)
    rango = last["high"].max() - last["low"].min()

    return rango < 0.002


# =========================
# 💥 RUPTURA FUERTE REAL
# =========================
def ruptura_fuerte(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    cuerpo = abs(last["close"] - last["open"])
    rango = last["high"] - last["low"]

    if cuerpo > (rango * 0.6):

        if last["close"] > prev["high"]:
            return "call"

        if last["close"] < prev["low"]:
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
# 📈 CONTINUIDAD (TU PATRÓN)
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
# ⭐ SCORE
# =========================
def score_calidad(df, direccion):
    score = 0
    last = df.iloc[-1]

    cuerpo = abs(last["close"] - last["open"])
    rango = last["high"] - last["low"]

    # fuerza
    if cuerpo > (rango * 0.6):
        score += 2

    # continuidad
    if continuidad(df, direccion):
        score += 2

    # vela limpia
    if vela_limpia(df):
        score += 1

    # penalizaciones
    if zona_repetida(df):
        score -= 2

    if rango > df["high"].rolling(20).mean().iloc[-1] * 1.5:
        score -= 2

    return score


# =========================
# 🚀 FUNCIÓN PRINCIPAL (CLAVE)
# =========================
def generate_signal(df):

    try:
        if len(df) < 30:
            return None

        # 1. lateralidad
        if not is_lateral(df):
            return None

        # 2. ruptura
        direccion = ruptura_fuerte(df)
        if not direccion:
            return None

        # 3. continuidad
        if not continuidad(df, direccion):
            return None

        # 4. evitar zonas malas
        if zona_repetida(df):
            return None

        # 5. score
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
