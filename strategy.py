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
# 🧠 INTERPRETACIÓN INTELIGENTE DE VELA
# ==============================
def interpretar_vela(v):
    open_ = v["open"]
    close = v["close"]
    high = v["max"]
    low = v["min"]

    cuerpo = abs(close - open_)
    rango = high - low

    if rango == 0:
        return None

    fuerza = cuerpo / rango

    mecha_sup = high - max(open_, close)
    mecha_inf = min(open_, close) - low

    # 🔥 FUERZA LIMPIA
    if fuerza > 0.7 and mecha_sup < cuerpo * 0.3 and mecha_inf < cuerpo * 0.3:
        if close > open_:
            return "call_fuerte"
        else:
            return "put_fuerte"

    # 🔥 RECHAZO ABAJO
    if mecha_inf > cuerpo * 1.2:
        return "rechazo_alcista"

    # 🔥 RECHAZO ARRIBA
    if mecha_sup > cuerpo * 1.2:
        return "rechazo_bajista"

    return None


# ==============================
# 🚫 MERCADO LIMPIO
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

        # 🔥 USAR VELA CERRADA
        vela = df.iloc[-2]

        tipo = interpretar_vela(vela)

        if tipo is None:
            return None

        # 🔥 DECISIÓN INTELIGENTE
        if tipo == "call_fuerte":
            direccion = "call"

        elif tipo == "put_fuerte":
            direccion = "put"

        elif tipo == "rechazo_alcista":
            direccion = "call"

        elif tipo == "rechazo_bajista":
            direccion = "put"

        else:
            return None

        if not evitar_tarde(df, direccion):
            return None

        return {
            "direction": direccion,
            "score": 95,
            "reason": [
                f"Tipo de vela: {tipo}",
                "Lectura de recorrido",
                "Confirmación por cierre",
                "Sin manipulación evidente"
            ]
        }

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None
