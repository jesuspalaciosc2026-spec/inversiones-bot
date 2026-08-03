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
# 🔥 VELA FUERTE (MEJORADA)
# ==============================
def vela_fuerte(v):
    cuerpo = abs(v["close"] - v["open"])
    rango = v["max"] - v["min"]

    if rango == 0:
        return False

    fuerza = cuerpo / rango

    mecha_superior = v["max"] - max(v["open"], v["close"])
    mecha_inferior = min(v["open"], v["close"]) - v["min"]

    if fuerza > 0.7 and mecha_superior < cuerpo * 0.4 and mecha_inferior < cuerpo * 0.4:
        return True

    return False


# ==============================
# ANALIZAR VELA
# ==============================
def analizar_vela(df):
    vela = df.iloc[-1]

    if not vela_fuerte(vela):
        return None

    if vela["close"] > vela["open"]:
        return "call"

    elif vela["close"] < vela["open"]:
        return "put"

    return None


# ==============================
# FILTRO IMPULSO (MENOS ESTRICTO)
# ==============================
def filtro_impulso(df):
    ultimas = df.tail(6)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    # 🔥 antes era 4 → ahora más flexible
    if alcistas >= 5 or bajistas >= 5:
        return False

    return True


# ==============================
# FILTRO ZONA
# ==============================
def filtro_zona(df):
    precio = df["close"].iloc[-1]

    max_60 = df["max"].tail(60).max()
    min_60 = df["min"].tail(60).min()

    if abs(precio - max_60) < (max_60 * 0.00015):
        return False

    if abs(precio - min_60) < (min_60 * 0.00015):
        return False

    return True


# ==============================
# FILTRO CONTINUIDAD (AJUSTADO)
# ==============================
def filtro_continuidad(df, direccion):
    ultimas = df.tail(3)

    if direccion == "call":
        if sum(ultimas["close"] > ultimas["open"]) < 1:
            return False

    if direccion == "put":
        if sum(ultimas["close"] < ultimas["open"]) < 1:
            return False

    return True


# ==============================
# FILTRO AGOTAMIENTO
# ==============================
def filtro_agotamiento(df):
    vela = df.iloc[-1]

    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return False

    if cuerpo < (rango * 0.4):
        return False

    return True


# ==============================
# FILTRO CONTRA TENDENCIA
# ==============================
def filtro_contra_tendencia(df, direccion):
    ultimas = df.tail(10)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    if bajistas >= 7 and direccion == "call":
        return False

    if alcistas >= 7 and direccion == "put":
        return False

    return True


# ==============================
# 🔥 CONFIRMACIÓN SNIPER (RÁPIDA)
# ==============================
def confirmacion_sniper(df, direccion):
    v1 = df.iloc[-3]
    v2 = df.iloc[-2]
    v3 = df.iloc[-1]  # vela en formación

    if not vela_fuerte(v1):
        return False

    if not vela_fuerte(v2):
        return False

    cuerpo_actual = abs(v3["close"] - v3["open"])
    rango_actual = v3["max"] - v3["min"]

    if rango_actual == 0:
        return False

    fuerza_actual = cuerpo_actual / rango_actual

    if direccion == "call":
        if (
            v1["close"] > v1["open"] and
            v2["close"] > v2["open"] and
            v3["close"] > v3["open"] and
            fuerza_actual > 0.55
        ):
            return True

    if direccion == "put":
        if (
            v1["close"] < v1["open"] and
            v2["close"] < v2["open"] and
            v3["close"] < v3["open"] and
            fuerza_actual > 0.55
        ):
            return True

    return False


# ==============================
# SEÑAL PRINCIPAL
# ==============================
def pro_signal(df, aggressive=True):
    try:
        if len(df) < 60:
            return None

        direccion = analizar_vela(df)

        if direccion is None:
            return None

        if not filtro_impulso(df):
            return None

        if not filtro_zona(df):
            return None

        if not filtro_continuidad(df, direccion):
            return None

        if not filtro_agotamiento(df):
            return None

        if not filtro_contra_tendencia(df, direccion):
            return None

        # 🔥 AQUÍ ESTÁ LA CLAVE
        if not confirmacion_sniper(df, direccion):
            return None

        return {
            "direction": direccion,
            "score": 90,
            "reason": [
                "Impulso confirmado",
                "Entrada anticipada",
                "Continuidad real",
                "Sniper activado"
            ]
        }

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None
