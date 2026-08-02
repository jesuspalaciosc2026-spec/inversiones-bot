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
# 📊 ESTRUCTURA (TENDENCIA)
# ==============================
def estructura_tendencia(df):
    ultimas = df.tail(6)

    maximos = list(ultimas["max"])
    minimos = list(ultimas["min"])

    # tendencia alcista
    if all(maximos[i] > maximos[i-1] for i in range(1, len(maximos))) and \
       all(minimos[i] > minimos[i-1] for i in range(1, len(minimos))):
        return "alcista"

    # tendencia bajista
    if all(maximos[i] < maximos[i-1] for i in range(1, len(maximos))) and \
       all(minimos[i] < minimos[i-1] for i in range(1, len(minimos))):
        return "bajista"

    return None


# ==============================
# 💪 VELA DE FUERZA (IMPULSO)
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
# 🔥 CONTINUIDAD
# ==============================
def continuidad(v_fuerza, v_actual, direccion):
    if direccion == "call":
        return (
            v_actual["close"] > v_actual["open"] and
            v_actual["close"] > v_fuerza["close"]
        )

    if direccion == "put":
        return (
            v_actual["close"] < v_actual["open"] and
            v_actual["close"] < v_fuerza["close"]
        )

    return False


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
# 🚀 SEÑAL PRINCIPAL
# ==============================
def pro_signal(df, aggressive=True):
    try:
        if len(df) < 60:
            return None

        tendencia = estructura_tendencia(df)

        if tendencia is None:
            return None

        v_fuerza = df.iloc[-2]
        v_actual = df.iloc[-1]

        motivos = []

        # ======================
        # 📈 CALL
        # ======================
        if tendencia == "alcista":

            if not vela_fuerza(v_fuerza):
                return None

            if not continuidad(v_fuerza, v_actual, "call"):
                return None

            if not evitar_tarde(df, "call"):
                return None

            motivos.append("Estructura alcista")
            motivos.append("Vela de impulso fuerte")
            motivos.append("Continuidad confirmada")
            motivos.append("Entrada en impulso")

            return {
                "direction": "call",
                "score": 50,
                "reason": motivos
            }

        # ======================
        # 📉 PUT
        # ======================
        if tendencia == "bajista":

            if not vela_fuerza(v_fuerza):
                return None

            if not continuidad(v_fuerza, v_actual, "put"):
                return None

            if not evitar_tarde(df, "put"):
                return None

            motivos.append("Estructura bajista")
            motivos.append("Vela de impulso fuerte")
            motivos.append("Continuidad confirmada")
            motivos.append("Entrada en impulso")

            return {
                "direction": "put",
                "score": 50,
                "reason": motivos
            }

        return None

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None
