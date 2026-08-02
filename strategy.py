import pandas as pd

# ==============================
# DETECTAR DOMINIO DE VELA
# ==============================
def analizar_vela(df):
    vela = df.iloc[-1]

    open_ = vela["open"]
    close = vela["close"]
    high = vela["max"]
    low = vela["min"]

    cuerpo = abs(close - open_)
    rango = high - low if high - low != 0 else 1

    fuerza = cuerpo / rango

    # Dominio claro
    if close > open_ and fuerza > 0.6:
        return "call", fuerza

    elif close < open_ and fuerza > 0.6:
        return "put", fuerza

    return None, 0


# ==============================
# DETECTAR ZONAS DE REVERSIÓN
# ==============================
def en_zona_reversion(df):
    df60 = df.tail(60)

    maximo = df60["max"].max()
    minimo = df60["min"].min()

    precio_actual = df.iloc[-1]["close"]

    # Si está cerca de extremos → NO operar
    if abs(precio_actual - maximo) < (df60["max"].std()):
        return True

    if abs(precio_actual - minimo) < (df60["min"].std()):
        return True

    return False


# ==============================
# DETECTAR IMPULSO FUERTE
# ==============================
def contar_impulso(df):
    count = 0

    for i in range(1, 7):
        vela = df.iloc[-i]

        if vela["close"] > vela["open"]:
            count += 1
        else:
            break

    return count


# ==============================
# FUNCIÓN PRINCIPAL
# ==============================
def pro_signal(df, aggressive=True):
    try:
        if df is None or len(df) < 70:
            return None, None, 0

        # 🔥 1. Evitar zonas peligrosas
        if en_zona_reversion(df):
            return None, None, 0

        # 🔥 2. Analizar vela actual
        direccion, fuerza = analizar_vela(df)

        if direccion is None:
            return None, None, 0

        # 🔥 3. Evitar final de impulso
        impulso = contar_impulso(df)

        if impulso >= 4:  # evita vela 4,5,6
            return None, None, 0

        # 🔥 4. Confirmación tendencia simple
        prev = df.iloc[-2]

        if direccion == "call" and prev["close"] > prev["open"]:
            score = 30 + (fuerza * 70)

        elif direccion == "put" and prev["close"] < prev["open"]:
            score = 30 + (fuerza * 70)

        else:
            score = 10

        # 🔥 5. Modo agresivo
        if aggressive:
            if score < 20:
                return None, None, 0
        else:
            if score < 40:
                return None, None, 0

        return direccion, "continuidad", int(score)

    except Exception as e:
        print(f"❌ ERROR estrategia: {e}")
        return None, None, 0


# ==============================
# RESULTADOS (PARA BOT)
# ==============================
def update_result(resultado):
    print(f"📊 Resultado operación: {resultado}")
