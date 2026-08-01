import pandas as pd
import numpy as np

# =============================
# INDICADORES
# =============================
def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    df["high_prev"] = df["high"].shift(1)
    df["low_prev"] = df["low"].shift(1)

    return df


# =============================
# TENDENCIA
# =============================
def detect_trend(df):
    last = df.iloc[-1]

    if last["ema20"] > last["ema50"]:
        return "up"
    elif last["ema20"] < last["ema50"]:
        return "down"
    else:
        return None


# =============================
# ESTRUCTURA (HH HL / LH LL)
# =============================
def market_structure(df):
    highs = df["high"].tail(5).values
    lows = df["low"].tail(5).values

    if all(x < y for x, y in zip(highs, highs[1:])) and all(x < y for x, y in zip(lows, lows[1:])):
        return "bullish"

    if all(x > y for x, y in zip(highs, highs[1:])) and all(x > y for x, y in zip(lows, lows[1:])):
        return "bearish"

    return None


# =============================
# PULLBACK SIMPLE
# =============================
def detect_pullback(df, trend):
    candles = df.tail(4)

    if trend == "up":
        return all(c["close"] < c["open"] for _, c in candles.iterrows())

    if trend == "down":
        return all(c["close"] > c["open"] for _, c in candles.iterrows())

    return False


# =============================
# VELA FUERTE
# =============================
def strong_candle(df, direction):
    c = df.iloc[-1]
    body = abs(c["close"] - c["open"])
    wick = (c["high"] - c["low"])

    if wick == 0:
        return False

    strength = body / wick

    if direction == "call":
        return c["close"] > c["open"] and strength > 0.6

    if direction == "put":
        return c["close"] < c["open"] and strength > 0.6

    return False


# =============================
# FILTRO DE RANGO
# =============================
def is_ranging(df):
    recent = df.tail(20)
    high = recent["high"].max()
    low = recent["low"].min()

    return (high - low) < (df["close"].mean() * 0.002)


# =============================
# ESTRATEGIA PRINCIPAL
# =============================
def pro_signal(df_m1, df_5s, aggressive=False):

    df_m1 = add_indicators(df_m1)

    trend = detect_trend(df_m1)
    structure = market_structure(df_m1)

    if trend is None or structure is None:
        return None, None, None

    if not aggressive:
        if is_ranging(df_m1):
            return None, None, None

    # =============================
    # CALL
    # =============================
    if trend == "up" and structure == "bullish":
        if detect_pullback(df_m1, "up"):
            if strong_candle(df_m1, "call"):
                return "call", 1, "pullback_up"

    # =============================
    # PUT
    # =============================
    if trend == "down" and structure == "bearish":
        if detect_pullback(df_m1, "down"):
            if strong_candle(df_m1, "put"):
                return "put", 1, "pullback_down"

    # =============================
    # MODO AGRESIVO (sin filtros duros)
    # =============================
    if aggressive:
        last = df_m1.iloc[-1]

        if last["close"] > last["open"]:
            return "call", 1, "aggressive"

        if last["close"] < last["open"]:
            return "put", 1, "aggressive"

    return None, None, None


# =============================
# RESULTADOS (GESTIÓN)
# =============================
stats = {
    "wins": 0,
    "loss": 0
}

def update_result(result, pattern):
    global stats

    if result == 1:
        stats["wins"] += 1
    else:
        stats["loss"] += 1

    print(f"📊 Resultado → {pattern} | Wins: {stats['wins']} | Loss: {stats['loss']}")
