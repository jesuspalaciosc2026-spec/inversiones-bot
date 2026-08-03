import numpy as np

# ==============================
# RESULTADOS
# ==============================
wins = 0
losses = 0

def update_result(result):
    global wins, losses

    if result > 0:
        wins += 1
    else:
        losses += 1

    print(f"📊 WIN: {wins} | LOSS: {losses}")


# ==============================
# 🔥 FUERZA REAL
# ==============================
def fuerza_real(vela):
    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return False

    fuerza = cuerpo / rango

    return fuerza > 0.75


# ==============================
# 🚫 EVITAR TRAMPAS
# ==============================
def evitar_trampa(vela):
    mecha_sup = vela["max"] - max(vela["open"], vela["close"])
    mecha_inf = min(vela["open"], vela["close"]) - vela["min"]

    cuerpo = abs(vela["close"] - vela["open"])

    if mecha_sup > cuerpo or mecha_inf > cuerpo:
        return False

    return True


# ==============================
# 🔥 CONFIRMACIÓN LIMPIA
# ==============================
def confirmacion_limpia(df):
    v1 = df.iloc[-3]
    v2 = df.iloc[-2]

    # ambas alcistas
    if v1["close"] > v1["open"] and v2["close"] > v2["open"]:
        mecha_sup1 = v1["max"] - v1["close"]
        mecha_sup2 = v2["max"] - v2["close"]

        cuerpo1 = abs(v1["close"] - v1["open"])
        cuerpo2 = abs(v2["close"] - v2["open"])

        if mecha_sup1 < cuerpo1 * 0.3 and mecha_sup2 < cuerpo2 * 0.3:
            return "call"

    # ambas bajistas
    if v1["close"] < v1["open"] and v2["close"] < v2["open"]:
        mecha_inf1 = v1["close"] - v1["min"]
        mecha_inf2 = v2["close"] - v2["min"]

        cuerpo1 = abs(v1["close"] - v1["open"])
        cuerpo2 = abs(v2["close"] - v2["open"])

        if mecha_inf1 < cuerpo1 * 0.3 and mecha_inf2 < cuerpo2 * 0.3:
            return "put"

    return None


# ==============================
# 🚫 ENTRAR TARDE
# ==============================
def evitar_tarde(df, direccion):
    ultimas = df.tail(5)

    if direccion == "call":
        return sum(ultimas["close"] > ultimas["open"]) < 4

    if direccion == "put":
        return sum(ultimas["close"] < ultimas["open"]) < 4

    return False


# ==============================
# 🧠 ENTRADA SNIPER
# ==============================
def entrada_sniper(df, direccion):
    ultima = df.iloc[-1]

    if direccion == "call":
        return ultima["close"] > ultima["open"]

    if direccion == "put":
        return ultima["close"] < ultima["open"]

    return False


# ==============================
# 🚀 SEÑAL PRINCIPAL
# ==============================
def pro_signal(df, aggressive=True):
    try:
        if len(df) < 60:
            return None

        # 🔥 Confirmación de continuidad
        direccion = confirmacion_limpia(df)

        if direccion is None:
            return None

        vela_confirmacion = df.iloc[-2]

        # 🔥 Filtros fuertes
        if not fuerza_real(vela_confirmacion):
            return None

        if not evitar_trampa(vela_confirmacion):
            return None

        if not evitar_tarde(df, direccion):
            return None

        # 🔥 Entrada sniper
        if not entrada_sniper(df, direccion):
            return None

        return {
            "direction": direccion,
            "score": 95,
            "reason": [
                "Continuidad confirmada (2 velas)",
                "Velas fuertes reales",
                "Sin mechas (sin manipulación)",
                "Entrada sniper confirmada"
            ]
        }

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None
