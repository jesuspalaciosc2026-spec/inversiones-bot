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
# ANALIZAR VELA (COMPLETA)
# ==============================
def analizar_vela(vela):
    open_ = vela["open"]
    close = vela["close"]
    high = vela["max"]
    low = vela["min"]

    cuerpo = abs(close - open_)
    rango = high - low

    if rango == 0:
        return None

    fuerza = cuerpo / rango

    mecha_arriba = high - max(open_, close)
    mecha_abajo = min(open_, close) - low

    return {
        "alcista": close > open_,
        "bajista": close < open_,
        "fuerza": fuerza,
        "mecha_arriba": mecha_arriba,
        "mecha_abajo": mecha_abajo,
        "rango": rango
    }


# ==============================
# TENDENCIA
# ==============================
def detectar_tendencia(df):
    ultimas = df.tail(5)

    highs = ultimas["max"].values
    lows = ultimas["min"].values

    alcista = all(highs[i] > highs[i-1] for i in range(1, len(highs)))
    bajista = all(lows[i] < lows[i-1] for i in range(1, len(lows)))

    if alcista:
        return "call"

    if bajista:
        return "put"

    return None


# ==============================
# FILTRO FUERZA REAL
# ==============================
def es_fuerza_real(info):
    if info is None:
        return False

    # cuerpo dominante
    if info["fuerza"] < 0.6:
        return False

    # evitar rechazo fuerte
    if info["alcista"] and info["mecha_abajo"] > info["rango"] * 0.4:
        return False

    if info["bajista"] and info["mecha_arriba"] > info["rango"] * 0.4:
        return False

    return True


# ==============================
# CONTINUIDAD LIMPIA
# ==============================
def es_continuidad(info, direccion):
    if info is None:
        return False

    if info["fuerza"] < 0.5:
        return False

    if direccion == "call":
        return info["alcista"]

    if direccion == "put":
        return info["bajista"]

    return False


# ==============================
# SEÑAL PRINCIPAL
# ==============================
def pro_signal(df):

    if len(df) < 10:
        return None

    # 🔥 IMPORTANTE:
    # -2 = vela CERRADA (confirmación real)
    # -3 = vela de impulso
    vela_fuerza = df.iloc[-3]
    vela_confirm = df.iloc[-2]

    info_fuerza = analizar_vela(vela_fuerza)
    info_confirm = analizar_vela(vela_confirm)

    if info_fuerza is None or info_confirm is None:
        return None

    # ==============================
    # TENDENCIA
    # ==============================
    direccion = detectar_tendencia(df)

    if direccion is None:
        return None

    # ==============================
    # FILTRO 1: FUERZA
    # ==============================
    if not es_fuerza_real(info_fuerza):
        return None

    # ==============================
    # FILTRO 2: DIRECCIÓN CORRECTA
    # ==============================
    if direccion == "call" and not info_fuerza["alcista"]:
        return None

    if direccion == "put" and not info_fuerza["bajista"]:
        return None

    # ==============================
    # FILTRO 3: CONTINUIDAD
    # ==============================
    if not es_continuidad(info_confirm, direccion):
        return None

    # ==============================
    # SEÑAL FINAL
    # ==============================
    return direccion, "continuidad_sniper", 100
