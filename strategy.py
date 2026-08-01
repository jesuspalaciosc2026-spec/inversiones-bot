import numpy as np

# ================= TICKS =================

def get_ticks(df_5s):
    return df_5s.tail(12)


# ================= EFICIENCIA =================

def efficiency(ticks):

    total_move = ticks.iloc[-1]["close"] - ticks.iloc[0]["open"]

    path = 0
    for i in range(1, len(ticks)):
        path += abs(ticks.iloc[i]["close"] - ticks.iloc[i-1]["close"])

    if path == 0:
        return 0

    return abs(total_move) / path


# ================= ESFUERZO VS RESULTADO =================

def effort_vs_result(ticks):

    total_move = abs(ticks.iloc[-1]["close"] - ticks.iloc[0]["open"])

    path = sum(abs(ticks.iloc[i]["close"] - ticks.iloc[i-1]["close"])
               for i in range(1, len(ticks)))

    if path == 0:
        return 0

    return total_move / path


# ================= TIEMPO EN ZONA =================

def time_in_zone(ticks):

    prices = ticks["close"].round(5)
    _, counts = np.unique(prices, return_counts=True)

    return counts.max()


# ================= MICRO RETROCESOS =================

def micro_pullbacks(ticks):

    changes = []

    for i in range(1, len(ticks)):
        diff = ticks.iloc[i]["close"] - ticks.iloc[i-1]["close"]
        changes.append(diff)

    reversals = 0

    for i in range(1, len(changes)):
        if changes[i] * changes[i-1] < 0:
            reversals += 1

    return reversals


# ================= PRESIÓN =================

def pressure(ticks):

    up = 0
    down = 0

    for i in range(len(ticks)):
        if ticks.iloc[i]["close"] > ticks.iloc[i]["open"]:
            up += 1
        else:
            down += 1

    return up, down


# ================= FUERZA REAL =================

def result_strength(ticks):

    open_p = ticks.iloc[0]["open"]
    close_p = ticks.iloc[-1]["close"]

    high = ticks["high"].max()
    low = ticks["low"].min()

    total = high - low

    if total == 0:
        return 0

    return abs(close_p - open_p) / total


# ================= FASES =================

def phase_analysis(ticks):

    p1 = ticks.iloc[0:3]
    p4 = ticks.iloc[9:12]

    m1 = p1["close"].iloc[-1] - p1["open"].iloc[0]
    m4 = p4["close"].iloc[-1] - p4["open"].iloc[0]

    s1 = np.mean(np.abs(np.diff(p1["close"])))
    s4 = np.mean(np.abs(np.diff(p4["close"])))

    return m1, m4, s1, s4


# ================= CIERRE DOMINANTE =================

def close_position(ticks):

    close = ticks.iloc[-1]["close"]
    high = ticks["high"].max()
    low = ticks["low"].min()

    if high == low:
        return 0.5

    return (close - low) / (high - low)


# ================= CONTEXTO =================

def short_context(df_5s):

    if len(df_5s) < 36:
        return 0

    last = df_5s.tail(36)
    closes = last["close"].values

    return closes[-1] - closes[0]


# ================= MANIPULACIÓN =================

def manipulation(ticks):

    last = ticks.iloc[-1]
    prev = ticks.iloc[-2]

    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return True

    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return True

    return False


# ================= SCORE =================

def score_candle(ticks, df_5s):

    eff = efficiency(ticks)
    evr = effort_vs_result(ticks)
    zone = time_in_zone(ticks)
    pullbacks = micro_pullbacks(ticks)
    up, down = pressure(ticks)
    strength = result_strength(ticks)
    m1, m4, s1, s4 = phase_analysis(ticks)
    cp = close_position(ticks)
    context = short_context(df_5s)

    total_move = ticks.iloc[-1]["close"] - ticks.iloc[0]["open"]

    score = 0
    direction = None

    # eficiencia
    if eff > 0.6:
        score += 10

    # esfuerzo vs resultado
    if evr > 0.6:
        score += 10
    elif evr < 0.4:
        score -= 10

    # fuerza
    if strength > 0.5:
        score += 10

    # ruido bajo
    if pullbacks <= 3:
        score += 10

    # no lateral
    if zone < 4:
        score += 10

    # aceleración
    if s4 > s1:
        score += 10

    # cierre dominante
    if cp > 0.7:
        score += 15
        direction = "call"

    elif cp < 0.3:
        score += 15
        direction = "put"

    # presión
    if total_move > 0 and up > down:
        score += 5

    if total_move < 0 and down > up:
        score += 5

    # contexto
    if context > 0 and direction == "call":
        score += 5

    if context < 0 and direction == "put":
        score += 5

    return score, direction, total_move, m1, m4


# ================= PRO SIGNAL =================

def pro_signal(df_m1, df_5s):

    if df_5s is None or len(df_5s) < 20:
        return None, None

    ticks = get_ticks(df_5s)

    # evitar manipulación directa
    if manipulation(ticks):
        return None, None

    score, direction, move, m1, m4 = score_candle(ticks, df_5s)

    # 🔥 UMBRAL
    if score < 65 or direction is None:
        return None, None

    # ================= CONTINUACIÓN =================

    if direction == "call" and move > 0 and m4 > m1:
        return "call", 1

    if direction == "put" and move < 0 and m4 < m1:
        return "put", 1

    # ================= ABSORCIÓN =================

    if move < 0 and direction == "call":
        return "call", 1

    if move > 0 and direction == "put":
        return "put", 1

    return None, None
