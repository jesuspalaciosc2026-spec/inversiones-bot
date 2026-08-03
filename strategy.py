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
# ANALISIS COMPLETO DE VELA
# ==============================
def analizar_vela_completa(vela):
    open_ = vela["open"]
    close = vela["close"]
    high = vela["max"]
    low = vela["min"]

    cuerpo = abs(close - open_)
    rango = high - low

    if rango == 0:
        return None

    # proporciones reales
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
# DETECTAR TENDENCIA REAL
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
# FILTRO DE FUERZA REAL
# ==============================
def es_fuerza_real(info):
    # 🔥 cuerpo dominante + poca mecha contraria
    if info["fuerza"] < 0.6:
        return False

    if info["alcista"] and info["mecha_abajo"] > info["rango"] * 0.4:
        return False

    if info["bajista"] and info["mecha_arriba"] > info["rango"] * 0.4:
        return False

    return True


# ==============================
# FILTRO CONTINUIDAD LIMPIA
# ==============================
def es_continuidad_limpia(info, direccion):
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

    # 🔥 vela de fuerza (cerrada)
    vela_fuerza = df.iloc[-2]

    # 🔥 vela actual (confirmación final)
    vela_confirm = df.iloc[-1]

    info_fuerza = analizar_vela_completa(vela_fuerza)
    info_confirm = analizar_vela_completa(vela_confirm)

    if info_fuerza is None or info_confirm is None:
        return None

    # ==============================
    # TENDENCIA
    # ==============================
    direccion = detectar_tendencia(df)

    if direccion is None:
        return None

    # ==============================
    # FILTRO 1: FUERZA REAL
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
    # FILTRO 3: CONTINUIDAD FINAL
    # ==============================
    if not es_continuidad_limpia(info_confirm, direccion):
        return None

    # ==============================
    # SEÑAL FINAL (COMPATIBLE CON BOT)
    # ==============================
    return direccion, "continuidad_sniper", 100
