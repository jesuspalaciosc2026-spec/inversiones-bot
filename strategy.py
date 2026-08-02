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
# ANALIZAR VELA
# ==============================
def analizar_vela(df):
    vela = df.iloc[-1]

    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return None

    fuerza = cuerpo / rango

    # Evitar indecisión
    if fuerza < 0.5:
        return None

    if vela["close"] > vela["open"]:
        return "call"

    elif vela["close"] < vela["open"]:
        return "put"

    return None


# ==============================
# FILTRO IMPULSO (NO ENTRAR TARDE)
# ==============================
def filtro_impulso(df):
    ultimas = df.tail(6)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    if alcistas >= 4 or bajistas >= 4:
        return False

    return True


# ==============================
# FILTRO ZONA (REVERSIÓN)
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

    if cuerpo < (rango * 0.4):
        return False

    return True


# ==============================
# 🔥 FILTRO CONTRA TENDENCIA (NUEVO)
# ==============================
def filtro_contra_tendencia(df, direccion):
    ultimas = df.tail(10)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    # Si venía bajista fuerte → NO CALL
    if bajistas >= 6 and direccion == "call":
        return False

    # Si venía alcista fuerte → NO PUT
    if alcistas >= 6 and direccion == "put":
        return False

    return True


# ==============================
# SEÑAL PRINCIPAL
# ==============================
def pro_signal(df, aggressive=True):
    try:
        if len(df) < 60:
            return None, None, 0

        # 1. Dirección de vela
        direccion = analizar_vela(df)

        if direccion is None:
            return None, None, 0

        # 2. Filtros
        if not filtro_impulso(df):
            return None, None, 0

        if not filtro_zona(df):
            return None, None, 0

        if not filtro_continuidad(df, direccion):
            return None, None, 0

        if not filtro_agotamiento(df):
            return None, None, 0

        if not filtro_contra_tendencia(df, direccion):
            return None, None, 0

        # 3. Score
        score = 30
        patron = "continuidad"

        return direccion, patron, score

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None, None, 0
