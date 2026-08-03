import numpy as np

# ==============================
# RESULTADOS
# ==============================
wins = 0
losses = 0

def update_result(result):
    global wins, losses

    try:
        result = float(result)
    except:
        result = 0

    if result > 0:
        wins += 1
    else:
        losses += 1

    print(f"📊 WIN: {wins} | LOSS: {losses}", flush=True)


# ==============================
# DETECTAR VELA FUERTE (SIN NUMEROS FIJOS)
# ==============================
def es_vela_fuerte(vela):
    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return False

    # 🔥 lógica más inteligente (no número fijo)
    if cuerpo > (rango * 0.6):
        return True

    return False


# ==============================
# EVITAR DOJI / INDECISIÓN
# ==============================
def es_indecision(vela):
    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return True

    if cuerpo < (rango * 0.3):
        return True

    return False


# ==============================
# DETECTAR CONTINUIDAD REAL
# ==============================
def detectar_continuidad(df):
    v1 = df.iloc[-3]
    v2 = df.iloc[-2]
    v3 = df.iloc[-1]

    # 🔥 EVITAR DOJI
    if es_indecision(v2) or es_indecision(v3):
        return None

    # ==============================
    # CALL (roja → 2 verdes fuertes)
    # ==============================
    if v1["close"] < v1["open"]:

        if (
            v2["close"] > v2["open"] and
            v3["close"] > v3["open"] and
            es_vela_fuerte(v2) and
            es_vela_fuerte(v3)
        ):
            return "call"

    # ==============================
    # PUT (verde → 2 rojas fuertes)
    # ==============================
    if v1["close"] > v1["open"]:

        if (
            v2["close"] < v2["open"] and
            v3["close"] < v3["open"] and
            es_vela_fuerte(v2) and
            es_vela_fuerte(v3)
        ):
            return "put"

    return None


# ==============================
# FILTRO DE TENDENCIA SUAVE
# ==============================
def filtro_tendencia(df, direccion):
    ultimas = df.tail(10)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    # 🔥 evita contra tendencia fuerte
    if direccion == "call" and bajistas > 7:
        return False

    if direccion == "put" and alcistas > 7:
        return False

    return True


# ==============================
# FILTRO ZONA (NO REBOTES)
# ==============================
def filtro_zona(df):
    precio = df["close"].iloc[-1]

    maximo = df["max"].tail(50).max()
    minimo = df["min"].tail(50).min()

    # 🔥 evitar extremos
    if abs(precio - maximo) < (maximo * 0.00015):
        return False

    if abs(precio - minimo) < (minimo * 0.00015):
        return False

    return True


# ==============================
# FILTRO IMPULSO (NO LLEGAR TARDE)
# ==============================
def filtro_impulso(df):
    ultimas = df.tail(6)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    # 🔥 evitar entrar tarde
    if alcistas >= 5 or bajistas >= 5:
        return False

    return True


# ==============================
# SEÑAL PRINCIPAL
# ==============================
def pro_signal(df, aggressive=True):
    try:
        if len(df) < 20:
            return None

        direccion = detectar_continuidad(df)

        if direccion is None:
            return None

        score = 50
        razon = []

        # ==============================
        # FILTROS (NO BLOQUEAN, SOLO RESTAN)
        # ==============================
        if not filtro_tendencia(df, direccion):
            score -= 20
            razon.append("Contra tendencia")

        if not filtro_zona(df):
            score -= 15
            razon.append("Zona peligrosa")

        if not filtro_impulso(df):
            score -= 10
            razon.append("Impulso agotado")

        # ==============================
        # SOLO ENTRADAS BUENAS
        # ==============================
        if score < 30:
            return None

        return direccion, "continuidad", score

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None
