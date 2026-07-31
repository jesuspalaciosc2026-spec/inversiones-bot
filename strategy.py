import numpy as np

# ================= UTILIDADES =================

def is_bullish(c):
    return c["close"] > c["open"]

def is_bearish(c):
    return c["close"] < c["open"]

def body(c):
    return abs(c["close"] - c["open"])

def rng(c):
    return c["high"] - c["low"]

# ================= TENDENCIA =================

def trend_m1(df):
    last = df.tail(5)
    bulls = sum(is_bullish(c) for _, c in last.iterrows())
    bears = sum(is_bearish(c) for _, c in last.iterrows())

    if bulls >= 4:
        return "call"
    if bears >= 4:
        return "put"
    return None


def trend_m5(df):
    last = df.tail(5)
    bulls = sum(is_bullish(c) for _, c in last.iterrows())
    bears = sum(is_bearish(c) for _, c in last.iterrows())

    if bulls >= 4:
        return "call"
    if bears >= 4:
        return "put"
    return None

# ================= ESTRUCTURA =================

def structure_ok(df, direction):
    highs = df["high"].tail(5).values
    lows = df["low"].tail(5).values

    if direction == "call":
        return all(highs[i] > highs[i-1] for i in range(1, len(highs))) and \
               all(lows[i] > lows[i-1] for i in range(1, len(lows)))

    if direction == "put":
        return all(highs[i] < highs[i-1] for i in range(1, len(highs))) and \
               all(lows[i] < lows[i-1] for i in range(1, len(lows)))

    return False

# ================= PULLBACK =================

def pullback(df, direction):
    candles = df.tail(4)

    if direction == "call":
        return sum(is_bearish(c) for _, c in candles.iterrows()) >= 2

    if direction == "put":
        return sum(is_bullish(c) for _, c in candles.iterrows()) >= 2

    return False

# ================= CONFIRMACIÓN =================

def strong_candle(c, direction):
    strength = body(c) / rng(c) if rng(c) > 0 else 0

    if direction == "call":
        return is_bullish(c) and strength > 0.6

    if direction == "put":
        return is_bearish(c) and strength > 0.6

    return False

# ================= FILTROS =================

def no_range(df):
    recent = df.tail(20)
    return (recent["high"].max() - recent["low"].min()) > (recent["high"] - recent["low"]).mean() * 2


def no_fake_break(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    return abs(last["close"] - prev["close"]) < (last["high"] - last["low"]) * 1.5


def far_from_levels(df):
    recent = df.tail(20)
    price = df["close"].iloc[-1]

    high = recent["high"].max()
    low = recent["low"].min()

    margin = (high - low) * 0.1

    return (low + margin) < price < (high - margin)

# ================= SCORE =================

def score_setup(df_m1, df_m5, direction):

    score = 0

    if trend_m5(df_m5) == direction:
        score += 2

    if trend_m1(df_m1) == direction:
        score += 2

    if structure_ok(df_m1, direction):
        score += 2

    if pullback(df_m1.iloc[:-1], direction):
        score += 1

    if strong_candle(df_m1.iloc[-1], direction):
        score += 2

    if no_range(df_m1):
        score += 1

    if no_fake_break(df_m1):
        score += 1

    if far_from_levels(df_m1):
        score += 1

    return score

# ================= MAIN =================

def pro_signal(df_m1, df_m5, df_htf=None):

    if len(df_m1) < 20 or len(df_m5) < 20:
        return None, None

    direction = trend_m1(df_m1)

    if direction is None:
        return None, None

    sc = score_setup(df_m1, df_m5, direction)

    # 🔥 SOLO ENTRADAS DE ALTA CALIDAD
    if sc >= 8:
        return direction, 1

    return None, None
