import numpy as np

# =========================================================
# 🧠 MEMORIA ADAPTATIVA
# =========================================================

trade_history = []


def update_result(result):
    trade_history.append(result)
    if len(trade_history) > 20:
        trade_history.pop(0)


def get_winrate():
    if len(trade_history) < 5:
        return 0.5
    return sum(trade_history) / len(trade_history)


# =========================================================
# ⚙️ ADAPTACIÓN DINÁMICA
# =========================================================

def dynamic_threshold():

    winrate = get_winrate()

    if winrate < 0.4:
        return 75
    elif winrate > 0.65:
        return 60

    return 65


def market_blocked():

    if len(trade_history) < 5:
        return False

    if trade_history[-3:] == [0, 0, 0]:
        return True

    return False


# =========================================================
# 📊 MICROESTRUCTURA
# =========================================================

def get_ticks(df_5s):
    return df_5s.tail(12)


def efficiency(ticks):

    move = ticks.iloc[-1]["close"] - ticks.iloc[0]["open"]

    path = sum(abs(ticks.iloc[i]["close"] - ticks.iloc[i-1]["close"])
               for i in range(1, len(ticks)))

    if path == 0:
        return 0

    return abs(move) / path


def pressure(ticks):

    up = sum(1 for i in range(len(ticks)) if ticks.iloc[i]["close"] > ticks.iloc[i]["open"])
    down = len(ticks) - up

    return up, down


def close_position(ticks):

    close = ticks.iloc[-1]["close"]
    high = ticks["high"].max()
    low = ticks["low"].min()

    if high == low:
        return 0.5

    return (close - low) / (high - low)


def manipulation(ticks):

    last = ticks.iloc[-1]
    prev = ticks.iloc[-2]

    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return True

    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return True

    return False


# =========================================================
# 🎯 SCORE
# =========================================================

def score_candle(ticks):

    eff = efficiency(ticks)
    cp = close_position(ticks)
    up, down = pressure(ticks)

    score = 0
    direction = None

    if eff > 0.6:
        score += 20

    if cp > 0.7:
        score += 25
        direction = "call"

    elif cp < 0.3:
        score += 25
        direction = "put"

    if up > down:
        score += 10
    else:
        score += 10

    return score, direction


# =========================================================
# 🚀 PRO SIGNAL
# =========================================================

def pro_signal(df_m1, df_5s):

    if market_blocked():
        return None, None

    if df_5s is None or len(df_5s) < 20:
        return None, None

    ticks = get_ticks(df_5s)

    if manipulation(ticks):
        return None, None

    score, direction = score_candle(ticks)

    threshold = dynamic_threshold()

    if score < threshold or direction is None:
        return None, None

    # =====================================================
    # 🔥 FILTROS PROFESIONALES
    # =====================================================

    last = df_m1.iloc[-1]

    # ---- 1. EVITAR VELA GRANDE (FOMO)
    candle_size = abs(last["close"] - last["open"])
    avg_size = (df_m1["high"] - df_m1["low"]).tail(10).mean()

    if candle_size > avg_size * 1.7:
        return None, None

    # ---- 2. EVITAR RECHAZO FUERTE (AGOTAMIENTO)
    upper_wick = last["high"] - max(last["close"], last["open"])
    lower_wick = min(last["close"], last["open"]) - last["low"]
    body = abs(last["close"] - last["open"])

    if direction == "call" and upper_wick > body * 1.5:
        return None, None

    if direction == "put" and lower_wick > body * 1.5:
        return None, None

    # ---- 3. EVITAR MÁXIMOS / MÍNIMOS
    last_price = last["close"]
    recent_high = df_m1["high"].tail(10).max()
    recent_low = df_m1["low"].tail(10).min()

    if direction == "call" and abs(last_price - recent_high) < 0.00015:
        return None, None

    if direction == "put" and abs(last_price - recent_low) < 0.00015:
        return None, None

    # ---- 4. EXIGIR PULLBACK
    last3 = df_m1.tail(3)

    if direction == "call":
        pullback = last3.iloc[-2]["close"] < last3.iloc[-3]["close"]
        if not pullback:
            return None, None

    if direction == "put":
        pullback = last3.iloc[-2]["close"] > last3.iloc[-3]["close"]
        if not pullback:
            return None, None

    # =====================================================
    # 🎯 ENTRADA FINAL
    # =====================================================

    return direction, 1
