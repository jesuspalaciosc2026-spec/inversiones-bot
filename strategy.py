import numpy as np

# ==============================
# RESULTADOS
# ==============================
wins = 0
losses = 0

def update_result(result):
    global wins, losses

    # 🔥 SEGURIDAD TOTAL
    if isinstance(result, tuple):
        result = result[0]

    if isinstance(result, str):
        if result.lower() == "win":
            result = 1
        elif result.lower() == "loose":
            result = -1
        else:
            result = 0

    if result > 0:
        wins += 1
    else:
        losses += 1

    print(f"📊 WIN: {wins} | LOSS: {losses}")


# ==============================
# 📊 TENDENCIA SIMPLE
# ==============================
def tendencia(df):
    ultimas = df.tail(10)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    if alcistas >= 5:
        return "call"

    if bajistas >= 5:
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

    return (cuerpo / rango) > 0.6


# ==============================
# 🚫 EVITAR LATERAL
# ==============================
def mercado_limpio(df):
    ultimas = df.tail(20)

    rango_total = ultimas["max"].max() - ultimas["min"].min()
    rango_promedio = (ultimas["max"] - ultimas["min"]).mean()

    return rango_total > (rango_promedio * 3)


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

        v1 = df.iloc[-2]
        v2 = df.iloc[-1]

        if not vela_fuerte(v1):
            return None

        # CALL
        if dir_tendencia == "call":
            if v2["close"] > v2["open"]:
                return {
                    "direction": "call",
                    "score": 70,
                    "reason": [
                        "Tendencia alcista",
                        "Impulso fuerte",
                        "Continuidad"
                    ]
                }

        # PUT
        if dir_tendencia == "put":
            if v2["close"] < v2["open"]:
                return {
                    "direction": "put",
                    "score": 70,
                    "reason": [
                        "Tendencia bajista",
                        "Impulso fuerte",
                        "Continuidad"
                    ]
                }

        return None

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None
