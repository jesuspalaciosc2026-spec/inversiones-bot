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
# 📊 ESTRUCTURA 5M
# ==============================
def estructura_tendencia(df):
    ultimas = df.tail(6)

    maximos = list(ultimas["max"])
    minimos = list(ultimas["min"])

    if all(maximos[i] > maximos[i-1] for i in range(1, len(maximos))) and \
       all(minimos[i] > minimos[i-1] for i in range(1, len(minimos))):
        return "alcista"

    if all(maximos[i] < maximos[i-1] for i in range(1, len(maximos))) and \
       all(minimos[i] < minimos[i-1] for i in range(1, len(minimos))):
        return "bajista"

    return None


# ==============================
# 💪 VELA DE IMPULSO 5M
# ==============================
def vela_fuerza(v):
    cuerpo = abs(v["close"] - v["open"])
    rango = v["max"] - v["min"]

    if rango == 0:
        return False

    fuerza = cuerpo / rango

    mecha_sup = v["max"] - max(v["close"], v["open"])
    mecha_inf = min(v["close"], v["open"]) - v["min"]

    return (
        fuerza > 0.7 and
        mecha_sup < cuerpo * 0.5 and
        mecha_inf < cuerpo * 0.5
    )


# ==============================
# 🚫 EVITAR IMPULSO TARDÍO
# ==============================
def evitar_tarde(df, direccion):
    ultimas = df.tail(5)

    if direccion == "call":
        return sum(ultimas["close"] > ultimas["open"]) < 4

    if direccion == "put":
        return sum(ultimas["close"] < ultimas["open"]) < 4

    return False


# ==============================
# 🔥 SEÑAL EN 5M (SOLO IMPULSO)
# ==============================
def signal_5m(df):
    try:
        if len(df) < 60:
            return None

        tendencia = estructura_tendencia(df)
        if tendencia is None:
            return None

        v_fuerza = df.iloc[-1]

        if not vela_fuerza(v_fuerza):
            return None

        motivos = []

        if tendencia == "alcista":
            direccion = "call"
            motivos.append("Estructura alcista 5M")

        elif tendencia == "bajista":
            direccion = "put"
            motivos.append("Estructura bajista 5M")

        else:
            return None

        if not evitar_tarde(df, direccion):
            return None

        motivos.append("Vela de impulso fuerte 5M")
        motivos.append("Inicio de impulso (no tardío)")

        return {
            "direction": direccion,
            "score": 50,
            "reason": motivos
        }

    except Exception as e:
        print("❌ ERROR 5M:", e)
        return None


# ==============================
# 🎯 CONFIRMACIÓN 1M (SNIPER)
# ==============================
def confirmacion_1m(df):
    v1 = df.iloc[-3]
    v2 = df.iloc[-2]
    v3 = df.iloc[-1]

    def fuerza(v):
        cuerpo = abs(v["close"] - v["open"])
        rango = v["max"] - v["min"]
        if rango == 0:
            return 0
        return cuerpo / rango

    def sin_mecha(v):
        cuerpo = abs(v["close"] - v["open"])
        mecha_sup = v["max"] - max(v["close"], v["open"])
        mecha_inf = min(v["close"], v["open"]) - v["min"]

        return mecha_sup < cuerpo * 0.5 and mecha_inf < cuerpo * 0.5

    # ======================
    # 📈 CALL
    # ======================
    if v1["close"] < v1["open"]:

        if (
            v2["close"] > v2["open"] and
            v3["close"] > v3["open"] and

            fuerza(v2) > 0.6 and
            fuerza(v3) > 0.7 and

            fuerza(v3) >= fuerza(v2) and

            sin_mecha(v2) and
            sin_mecha(v3) and

            v3["close"] > v2["close"]
        ):
            return "call"

    # ======================
    # 📉 PUT
    # ======================
    if v1["close"] > v1["open"]:

        if (
            v2["close"] < v2["open"] and
            v3["close"] < v3["open"] and

            fuerza(v2) > 0.6 and
            fuerza(v3) > 0.7 and

            fuerza(v3) >= fuerza(v2) and

            sin_mecha(v2) and
            sin_mecha(v3) and

            v3["close"] < v2["close"]
        ):
            return "put"

    return None
