# ==============================
# RESULTADOS
# ==============================
wins = 0
losses = 0

def update_result(result):
    global wins, losses

    if isinstance(result, tuple):
        result = result[0]

    if isinstance(result, str):
        result = float(result)

    if result > 0:
        wins += 1
    else:
        losses += 1

    print(f"📊 WIN: {wins} | LOSS: {losses}")


# ==============================
# DETECCIÓN DE FUERZA (SIN NÚMEROS FIJOS)
# ==============================
def es_vela_fuerte(df, index):
    vela = df.iloc[index]

    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return False

    # Comparación con velas anteriores (dinámico)
    ultimas = df.iloc[index-5:index]

    cuerpos_previos = abs(ultimas["close"] - ultimas["open"])
    promedio = cuerpos_previos.mean()

    # 👉 Fuerza relativa (NO número fijo)
    if cuerpo > promedio:
        return True

    return False


# ==============================
# DETECCIÓN DE INDECISIÓN
# ==============================
def es_indecision(df, index):
    vela = df.iloc[index]

    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return True

    # Comparación relativa
    ultimas = df.iloc[index-5:index]
    cuerpos_previos = abs(ultimas["close"] - ultimas["open"])
    promedio = cuerpos_previos.mean()

    return cuerpo < promedio


# ==============================
# FILTRO DE TENDENCIA (SIN NÚMEROS)
# ==============================
def detectar_tendencia(df):
    ultimas = df.tail(10)

    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    if alcistas > bajistas:
        return "alcista"
    elif bajistas > alcistas:
        return "bajista"

    return None


# ==============================
# FILTRO IMPULSO
# ==============================
def filtro_impulso(df):
    ultimas = df.tail(6)

    cambios = abs(ultimas["close"] - ultimas["open"])
    promedio = cambios.mean()

    # Evitar mercado muerto
    return promedio > 0


# ==============================
# FILTRO ZONA
# ==============================
def filtro_zona(df):
    precio = df["close"].iloc[-1]

    maximo = df["max"].tail(50).max()
    minimo = df["min"].tail(50).min()

    rango = maximo - minimo

    if rango == 0:
        return False

    # Evitar extremos (dinámico)
    posicion = (precio - minimo) / rango

    if posicion > 0.9 or posicion < 0.1:
        return False

    return True


# ==============================
# FILTRO CONTINUIDAD
# ==============================
def filtro_continuidad(df, direccion):
    ultimas = df.tail(4)

    if direccion == "call":
        return sum(ultimas["close"] > ultimas["open"]) >= 2

    if direccion == "put":
        return sum(ultimas["close"] < ultimas["open"]) >= 2

    return False


# ==============================
# FILTRO CONTRA TENDENCIA
# ==============================
def filtro_contra_tendencia(df, direccion):
    tendencia = detectar_tendencia(df)

    if tendencia is None:
        return False

    if tendencia == "alcista" and direccion == "put":
        return False

    if tendencia == "bajista" and direccion == "call":
        return False

    return True


# ==============================
# 🔥 PATRÓN SNIPER MEJORADO
# ==============================
def patron_sniper(df):
    if len(df) < 6:
        return None

    v1 = df.iloc[-3]
    v2 = df.iloc[-2]
    v3 = df.iloc[-1]

    # CALL
    if v1["close"] < v1["open"]:

        if es_vela_fuerte(df, -2) and es_vela_fuerte(df, -1):
            if v2["close"] > v2["open"] and v3["close"] > v3["open"]:
                if not es_indecision(df, -2) and not es_indecision(df, -1):
                    return "call"

    # PUT
    if v1["close"] > v1["open"]:

        if es_vela_fuerte(df, -2) and es_vela_fuerte(df, -1):
            if v2["close"] < v2["open"] and v3["close"] < v3["open"]:
                if not es_indecision(df, -2) and not es_indecision(df, -1):
                    return "put"

    return None


# ==============================
# 🔥 SEÑAL FINAL
# ==============================
def pro_signal(df, aggressive=True):
    try:
        if len(df) < 60:
            return None, None, 0

        direccion = patron_sniper(df)

        if direccion is None:
            return None, None, 0

        if not filtro_impulso(df):
            return None, None, 0

        if not filtro_zona(df):
            return None, None, 0

        if not filtro_continuidad(df, direccion):
            return None, None, 0

        if not filtro_contra_tendencia(df, direccion):
            return None, None, 0

        score = 90
        patron = "sniper_inteligente"

        return direccion, patron, score

    except Exception as e:
        print("❌ ERROR estrategia:", e)
        return None, None, 0
