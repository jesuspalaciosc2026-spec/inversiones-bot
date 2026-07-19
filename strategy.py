import numpy as np
import pandas as pd

# ================= INDICADORES (MEJORADOS) =================
def add_indicators(df):
    df = df.copy().reset_index(drop=True)

    # EMA 20 con cálculo exacto
    df["ema20"] = df["close"].ewm(span=20, adjust=False, min_periods=20).mean()

    # ATR 14 CÁLCULO ESTÁNDAR (antes tenía error en la serie)
    df["high_low"] = df["high"] - df["low"]
    df["high_close"] = abs(df["high"] - df["close"].shift(1))
    df["low_close"] = abs(df["low"] - df["close"].shift(1))
    df["tr"] = df[["high_low", "high_close", "low_close"]].max(axis=1)
    df["atr"] = df["tr"].rolling(window=14, min_periods=14).mean()

    # Indicador extra para confirmar tendencia de entrada
    df["ema5"] = df["close"].ewm(span=5, adjust=False, min_periods=5).mean()

    return df

# ================= ZONA HTF (MÁS FIABLE) =================
def get_zone(df_htf):
    # Usamos min_periods para no fallar con datos incompletos
    highs = df_htf["high"].rolling(window=20, min_periods=15).max()
    lows = df_htf["low"].rolling(window=20, min_periods=15).min()

    resistance = round(highs.iloc[-1], 5)
    support = round(lows.iloc[-1], 5)

    return support, resistance

# ================= DOBLE TEST (MÁS EXACTO) =================
def double_touch(df_m5, level, is_support=True):
    # Solo revisamos velas cerradas (no la última en formación)
    revisar = df_m5.iloc[-12:-1]
    touches = 0

    for _, candle in revisar.iterrows():
        if is_support:
            # Rechazo claro: toca el soporte y cierra por encima
            if candle["low"] <= level and candle["close"] > level:
                touches += 1
        else:
            # Rechazo claro: toca la resistencia y cierra por debajo
            if candle["high"] >= level and candle["close"] < level:
                touches += 1

    return touches >= 2

# ================= CONFIRMACIÓN DE ENTRADA (MEJORADA PARA 1M) =================
def confirmation(df_m1, direction, level):
    # Últimas 2 velas cerradas de 1 minuto
    vela_actual = df_m1.iloc[-1]
    vela_anterior = df_m1.iloc[-2]

    if direction == "call":
        # Tendencia alcista + vela verde fuerte + cierra por encima del nivel
        return (
            vela_actual["close"] > vela_actual["open"]
            and vela_actual["close"] > vela_anterior["close"]
            and vela_actual["close"] > level
            and (vela_actual["close"] - vela_actual["open"]) > (vela_actual["atr"] * 0.3)
        )

    if direction == "put":
        # Tendencia bajista + vela roja fuerte + cierra por debajo del nivel
        return (
            vela_actual["close"] < vela_actual["open"]
            and vela_actual["close"] < vela_anterior["close"]
            and vela_actual["close"] < level
            and (vela_actual["open"] - vela_actual["close"]) > (vela_actual["atr"] * 0.3)
        )

    return False

# ================= SEÑAL FINAL (EXCLUSIVO EXPIRACIÓN 1 MINUTO) =================
def pro_signal(df_m1, df_m5, df_htf):
    # Validación de datos mínimos
    min_velas_htf = 20
    min_velas_m5 = 15
    min_velas_m1 = 10

    if len(df_htf) < min_velas_htf or len(df_m5) < min_velas_m5 or len(df_m1) < min_velas_m1:
        return None, None, None

    # Añadimos indicadores si no existen
    if "atr" not in df_m1.columns:
        df_m1 = add_indicators(df_m1)
    if "atr" not in df_m5.columns:
        df_m5 = add_indicators(df_m5)

    support, resistance = get_zone(df_htf)
    precio_actual = round(df_m1["close"].iloc[-1], 5)
    atr_actual = df_m1["atr"].iloc[-1]

    if np.isnan(atr_actual) or atr_actual <= 0:
        return None, None, None

    # Margen dinámico ajustado para entradas exactas
    buffer = round(atr_actual * 0.8, 5)

    # ========== SEÑAL COMPRA (CALL) - EXPIRACIÓN 1M ==========
    if abs(precio_actual - support) <= buffer:
        if double_touch(df_m5, support, is_support=True):
            if confirmation(df_m1, "call", support):
                # Devolvemos dirección, expiración FIJA y confianza
                return "call", 1, "✅ SEÑAL CALL | SOPORTE | EXP: 1M"

    # ========== SEÑAL VENTA (PUT) - EXPIRACIÓN 1M ==========
    if abs(precio_actual - resistance) <= buffer:
        if double_touch(df_m5, resistance, is_support=False):
            if confirmation(df_m1, "put", resistance):
                return "put", 1, "✅ SEÑAL PUT | RESISTENCIA | EXP: 1M"

    return None, None, "⏳ ESPERANDO MEJOR ENTRADA"
