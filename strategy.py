import numpy as np

=========================================================

================= INDICADORES ============================

=========================================================

def add_indicators(df):
df = df.copy()

# EMA 20
df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()

# ATR 14
high_low = df["high"] - df["low"]
high_close = abs(df["high"] - df["close"].shift())
low_close = abs(df["low"] - df["close"].shift())

df["tr"] = np.maximum(high_low, np.maximum(high_close, low_close))
df["atr"] = df["tr"].rolling(14).mean()

return df

=========================================================

================= ZONA HTF ===============================

=========================================================

def get_zone(df_htf):
highs = df_htf["high"].rolling(20).max()
lows = df_htf["low"].rolling(20).min()

resistance = highs.iloc[-1]
support = lows.iloc[-1]

return support, resistance

=========================================================

================= DOBLE TEST =============================

=========================================================

def double_touch(df_m5, level, atr, is_support=True):
touches = 0
tolerance = atr * 0.5

for i in range(-10, 0):
    candle = df_m5.iloc[i]

    if is_support:
        if abs(candle["low"] - level) <= tolerance:
            touches += 1
    else:
        if abs(candle["high"] - level) <= tolerance:
            touches += 1

return touches >= 2

=========================================================

================= SEÑAL PRINCIPAL ========================

=========================================================

def pro_signal(df_m1, df_m5, df_htf):

if len(df_htf) < 20 or len(df_m1) < 20 or len(df_m5) < 10:
    return None, None

df_m1 = add_indicators(df_m1)
df_m5 = add_indicators(df_m5)

support, resistance = get_zone(df_htf)

price = df_m1["close"].iloc[-1]
atr = df_m1["atr"].iloc[-1]

if np.isnan(atr):
    return None, None

buffer = atr * 1.2

ema = df_m1["ema20"].iloc[-1]
trend_up = price > ema
trend_down = price < ema

last = df_m1.iloc[-1]
body = abs(last["close"] - last["open"])

# =====================================================
# 🟩 1. CONTINUIDAD (PRIORIDAD ALTA)
# =====================================================

# Breakout alcista fuerte
if price > resistance + buffer and trend_up:
    if last["close"] > last["open"] and body > atr * 0.3:
        return "call", 60

# Breakout bajista fuerte
if price < support - buffer and trend_down:
    if last["close"] < last["open"] and body > atr * 0.3:
        return "put", 60

# =====================================================
# 🟥 2. REVERSIÓN (SOLO SI NO HUBO BREAKOUT)
# =====================================================

# rechazo = vela con mecha larga
upper_wick = last["high"] - max(last["open"], last["close"])
lower_wick = min(last["open"], last["close"]) - last["low"]

# -------- SOPORTE --------
if abs(price - support) <= buffer:

    rejection = lower_wick > body * 1.5

    if rejection and not trend_down:
        if double_touch(df_m5, support, atr, True):
            return "call", 60

# -------- RESISTENCIA --------
if abs(price - resistance) <= buffer:

    rejection = upper_wick > body * 1.5

    if rejection and not trend_up:
        if double_touch(df_m5, resistance, atr, False):
            return "put", 60

return None, None

=========================================================

================= EJEMPLO DE USO =========================

=========================================================

if name == "main":
# Debes cargar tus DataFrames aquí:
# df_m1, df_m5, df_htf

# Ejemplo de ejecución:
# signal, expiry = pro_signal(df_m1, df_m5, df_htf)
# if signal:
#     print(f"Señal: {signal} | Expiración: {expiry}s")

pass
