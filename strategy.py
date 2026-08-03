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
# 🔥 VELA FUERTE (PRECISA)
# ==============================
def vela_fuerte(v):
    cuerpo = abs(v["close"] - v["open"])
    rango = v["max"] - v["min"]

    if rango == 0:
        return False

    fuerza = cuerpo / rango

    mecha_sup = v["max"] - max(v["close"], v["open"])
    mecha_inf = min(v["close"], v["open"]) - v["min"]

    # 🔥 FILTRO DE PRECISIÓN
    return (
        fuerza > 0.7 and
        mecha_sup < cuerpo * 0.3 and
        mecha_inf < cuerpo * 0.3
    )


# ==============================
# 📊 ANALIZAR VELA CERRADA
# ==============================
def analizar_cierre(df):
    vela = df.iloc[-2]  # 🔥 VELA CERRADA REAL

    if not vela_fuerte(vela):
        return None

    if vela["close"] > vela["open"]:
        return "call"

    elif vela["close"] < vela["open"]:
        return "put"

    return None


# ==============================
# 🚫 EVITAR MERCADO LATERAL
# ==============================
def mercado_limpio(df):
    ultimas = df.tail(20)

    rango_total = ultimas["max"].max() - ultimas["min"].min()
    rango_promedio = (ultimas["max"] - ultimas["min"]).mean()

    return rango_total > rango_promedio * 3


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
        if len(df) < 60:
            return None

        if not mercado_limpio(df):
            return None

        direccion = analizar_cierre(df)

        if direccion is None:
            return None

        if not evitar_tarde(df, direccion):
            return None

        return {
            "direction": direccion,
            "score": 95,
            "reason": [
                "Vela cerrada fuerte",
                "Confirmación real",
                "Sin mechas débiles",
                "Entrada en nueva vela"
            ]
        }

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None
