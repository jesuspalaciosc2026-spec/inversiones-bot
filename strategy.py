import numpy as np

# ==============================
# RESULTADOS
# ==============================
wins = 0
losses = 0

def update_result(result):
    global wins, losses

    if isinstance(result, tuple):
        result = result[0]

    if result > 0:
        wins += 1
    else:
        losses += 1

    print(f"📊 WIN: {wins} | LOSS: {losses}")


# ==============================
# 📊 DETECTAR DIRECCIÓN GENERAL
# ==============================
def tendencia(df):
    ultimas = df.tail(10)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    if alcistas >= 6:
        return "call"

    if bajistas >= 6:
        return "put"

    return None


# ==============================
# 💪 VELA FUERTE
# ==============================
def vela_fuerte(v):
    cuerpo = abs(v["close"] - v["open"])
    rango = v["max"] - v["min"]

    if rango == 0:
        return False

    fuerza = cuerpo / rango

    mecha_sup = v["max"] - max(v["close"], v["open"])
    mecha_inf = min(v["close"], v["open"]) - v["min"]

    return (
        fuerza > 0.6 and
        mecha_sup < cuerpo and
        mecha_inf < cuerpo
    )


# ==============================
# 🚫 EVITAR LATERALIDAD
# ==============================
def mercado_limpio(df):
    ultimas = df.tail(20)

    rango_total = ultimas["max"].max() - ultimas["min"].min()
    rango_promedio = (ultimas["max"] - ultimas["min"]).mean()

    if rango_total < rango_promedio * 4:
        return False

    return True


# ==============================
# 🚫 EVITAR ENTRAR TARDE
# ==============================
def evitar_tarde(df, direccion):
    ultimas = df.tail(5)

    if direccion == "call":
        return sum(ultimas["close"] > ultimas["open"]) < 4

    if direccion == "put":
        return sum(ultimas["close"] < ultimas["open"]) < 4

    return False


# ==============================
# 🚀 SEÑAL PRINCIPAL
# ==============================
def pro_signal(df, aggressive=True):
    try:
        if len(df) < 50:
            return None

        if not mercado_limpio(df):
            return None

        dir_tendencia = tendencia(df)
        if dir_tendencia is None:
            return None

        v1 = df.iloc[-2]  # vela de impulso
        v2 = df.iloc[-1]  # confirmación

        if not vela_fuerte(v1):
            return None

        # ======================
        # 📈 CALL
        # ======================
        if dir_tendencia == "call":

            if not (v2["close"] > v2["open"]):
                return None

            if not evitar_tarde(df, "call"):
                return None

            return {
                "direction": "call",
                "score": 70,
                "reason": [
                    "Tendencia alcista",
                    "Vela fuerte",
                    "Continuidad confirmada"
                ]
            }

        # ======================
        # 📉 PUT
        # ======================
        if dir_tendencia == "put":

            if not (v2["close"] < v2["open"]):
                return None

            if not evitar_tarde(df, "put"):
                return None

            return {
                "direction": "put",
                "score": 70,
                "reason": [
                    "Tendencia bajista",
                    "Vela fuerte",
                    "Continuidad confirmada"
                ]
            }

        return None

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None
