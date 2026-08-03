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
# 📊 ESTRUCTURA (5M)
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
# 💪 VELA DE IMPULSO (5M)
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
# 🔥 SEÑAL 5M (IMPULSO)
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

        if tendencia == "alcista":
            direccion = "call"
        else:
            direccion = "put"

        if not evitar_tarde(df, direccion):
            return None

        return {
            "direction": direccion,
            "score": 50,
            "reason": [
                f"Estructura {tendencia}",
                "Impulso fuerte 5M",
                "Entrada en continuidad"
            ]
        }

    except Exception as e:
        print("❌ ERROR 5M:", e)
        return None


# ==============================
# 🎯 CONFIRMACIÓN 1M OPTIMIZADA
# ==============================
def confirmacion_1m(df, direccion):
    ultimas = df.tail(5)

    def fuerza(v):
        cuerpo = abs(v["close"] - v["open"])
        rango = v["max"] - v["min"]
        if rango == 0:
            return 0
        return cuerpo / rango

    for i in range(len(ultimas)):
        v = ultimas.iloc[i]

        if direccion == "call":
            if (
                v["close"] > v["open"] and
                fuerza(v) > 0.6
            ):
                return True

        if direccion == "put":
            if (
                v["close"] < v["open"] and
                fuerza(v) > 0.6
            ):
                return True

    return False
