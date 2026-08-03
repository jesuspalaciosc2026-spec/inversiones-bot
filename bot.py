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

    # 🔥 PRECISIÓN EXTREMA SIN CAMBIAR LÓGICA
    if fuerza > 0.75 and mecha_superior < cuerpo * 0.3 and mecha_inferior < cuerpo * 0.3:
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
# FILTRO IMPULSO
# ==============================
def filtro_impulso(df):
    ultimas = df.tail(6)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    if alcistas >= 4 or bajistas >= 4:
        return False

    return True


# ==============================
# FILTRO ZONA
# ==============================
def filtro_zona(df):
    precio = df["close"].iloc[-1]

    max_60 = df["max"].tail(60).max()
    min_60 = df["min"].tail(60).min()

    if abs(precio - max_60) < (max_60 * 0.0002):
        return False

    if abs(precio - min_60) < (min_60 * 0.0002):
        return False

    return True


# ==============================
# FILTRO CONTINUIDAD
# ==============================
def filtro_continuidad(df, direccion):
    ultimas = df.tail(4)

    if direccion == "call":
        if sum(ultimas["close"] > ultimas["open"]) < 2:
            return False

    if direccion == "put":
        if sum(ultimas["close"] < ultimas["open"]) < 2:
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

    if cuerpo < (rango * 0.5):
        return False

    return True


# ==============================
# FILTRO CONTRA TENDENCIA
# ==============================
def filtro_contra_tendencia(df, direccion):
    ultimas = df.tail(10)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    if bajistas >= 6 and direccion == "call":
        return False

    if alcistas >= 6 and direccion == "put":
        return False

    return True


# ==============================
# 🔥 CONFIRMACIÓN 2 VELAS (SNIPER)
# ==============================
def confirmacion_sniper(df, direccion):
    v1 = df.iloc[-2]
    v2 = df.iloc[-1]

    if not vela_fuerte(v1) or not vela_fuerte(v2):
        return False

    if direccion == "call":
        if v1["close"] > v1["open"] and v2["close"] > v2["open"]:
            return True

    if direccion == "put":
        if v1["close"] < v1["open"] and v2["close"] < v2["open"]:
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

        # 🔥 CONFIRMACIÓN FINAL (PRECISIÓN)
        if not confirmacion_sniper(df, direccion):
            return None

        return {
            "direction": direccion,
            "score": 95,
            "reason": [
                "Vela fuerte confirmada",
                "Continuidad limpia",
                "Sin mechas débiles",
                "Confirmación doble sniper",
                "Sin manipulación"
            ]
        }

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None
