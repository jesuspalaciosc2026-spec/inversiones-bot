# ==============================
# STRATEGY ULTRA WINRATE
# SOLO CONTINUIDAD + TENDENCIA
# ==============================

def es_fuerza_real(vela):
    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return False

    ratio = cuerpo / rango

    # 🔥 cuerpo dominante (sin indecisión)
    return ratio > 0.7


def es_continuidad(vela, direccion):
    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return False

    ratio = cuerpo / rango

    # 🔥 vela limpia, sin ruido
    if ratio < 0.6:
        return False

    if direccion == "call":
        return vela["close"] > vela["open"]

    if direccion == "put":
        return vela["close"] < vela["open"]

    return False


def tendencia(df):
    ultimas = df.tail(5)

    highs = ultimas["max"].values
    lows = ultimas["min"].values

    # 🔥 máximos crecientes
    alcista = all(highs[i] > highs[i - 1] for i in range(1, len(highs)))

    # 🔥 mínimos decrecientes
    bajista = all(lows[i] < lows[i - 1] for i in range(1, len(lows)))

    if alcista:
        return "call"

    if bajista:
        return "put"

    return None


# ==============================
# SEÑAL PRINCIPAL
# ==============================
def pro_signal(df):

    if len(df) < 10:
        return None

    vela_fuerza = df.iloc[-2]
    vela_confirm = df.iloc[-1]

    dir_trend = tendencia(df)

    # ❌ sin tendencia = no operar
    if dir_trend is None:
        return None

    # ==============================
    # FILTRO 1: VELA DE FUERZA REAL
    # ==============================
    if not es_fuerza_real(vela_fuerza):
        return None

    # ==============================
    # FILTRO 2: DIRECCIÓN CORRECTA
    # ==============================
    if dir_trend == "call" and vela_fuerza["close"] <= vela_fuerza["open"]:
        return None

    if dir_trend == "put" and vela_fuerza["close"] >= vela_fuerza["open"]:
        return None

    # ==============================
    # FILTRO 3: CONTINUIDAD LIMPIA
    # ==============================
    if not es_continuidad(vela_confirm, dir_trend):
        return None

    # 🔥 SEÑAL FINAL
    return dir_trend, "continuidad", "ALTA"


# ==============================
# RESULTADOS (IA simple)
# ==============================
wins = 0
losses = 0


def update_result(result):
    global wins, losses

    if result > 0:
        wins += 1
    else:
        losses += 1

    print(f"📊 WIN: {wins} | LOSS: {losses}", flush=True)
