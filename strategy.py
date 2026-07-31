import numpy as np

# ================= RECONSTRUIR VELA =================

def build_candle_from_ticks(df_5s):

    ticks = df_5s.tail(12)

    open_price = ticks.iloc[0]["open"]
    close_price = ticks.iloc[-1]["close"]
    high = ticks["high"].max()
    low = ticks["low"].min()

    return open_price, close_price, high, low


# ================= DOMINANCIA =================

def dominance(df_5s):

    ticks = df_5s.tail(12)

    buyers = 0
    sellers = 0
    strength = 0

    for i in range(len(ticks)):
        c = ticks.iloc[i]

        move = c["close"] - c["open"]
        size = abs(move)
        full = c["high"] - c["low"]

        if full == 0:
            continue

        power = size / full

        if move > 0:
            buyers += 1
            strength += power
        else:
            sellers += 1
            strength -= power

    return buyers, sellers, strength


# ================= MANIPULACIÓN =================

def manipulation(df_5s):

    ticks = df_5s.tail(6)

    highs = ticks["high"].values
    lows = ticks["low"].values
    closes = ticks["close"].values

    if highs[-1] > max(highs[:-1]) and closes[-1] < highs[-2]:
        return True

    if lows[-1] < min(lows[:-1]) and closes[-1] > lows[-2]:
        return True

    return False


# ================= VELOCIDAD =================

def velocity(df_5s):

    ticks = df_5s.tail(6)

    movements = []

    for i in range(1, len(ticks)):
        diff = ticks.iloc[i]["close"] - ticks.iloc[i-1]["close"]
        movements.append(diff)

    return np.mean(np.abs(movements))


# ================= PRO SIGNAL =================

def pro_signal(df_m1, df_5s):

    if df_m1 is None or df_5s is None:
        return None, None

    if len(df_5s) < 20:
        return None, None

    open_p, close_p, high, low = build_candle_from_ticks(df_5s)

    body = close_p - open_p
    total = high - low

    if total == 0:
        return None, None

    body_strength = abs(body) / total

    buyers, sellers, strength = dominance(df_5s)

    # filtros
    if manipulation(df_5s):
        return None, None

    if velocity(df_5s) < 0.00001:
        return None, None

    # CONTINUACIÓN
    if body > 0 and buyers > sellers and strength > 0.5 and body_strength > 0.5:
        return "call", 1

    if body < 0 and sellers > buyers and strength < -0.5 and body_strength > 0.5:
        return "put", 1

    # REVERSIÓN
    if body > 0 and sellers > buyers:
        return "put", 1

    if body < 0 and buyers > sellers:
        return "call", 1

    return None, None
