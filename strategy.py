import json
import os

MEMORY_FILE = "ai_memory.json"

# =========================================================
# 🧠 MEMORIA IA
# =========================================================

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "wins": 0,
            "losses": 0,
            "confidence": 1.0
        }

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f)


# =========================================================
# 🧠 CONTEXTO (M1)
# =========================================================

def get_context(df):

    highs = df["high"].tail(5).values
    lows = df["low"].tail(5).values

    bullish = all(highs[i] > highs[i-1] for i in range(1, len(highs))) and \
              all(lows[i] > lows[i-1] for i in range(1, len(lows)))

    bearish = all(highs[i] < highs[i-1] for i in range(1, len(highs))) and \
              all(lows[i] < lows[i-1] for i in range(1, len(lows)))

    if bullish:
        return "call"

    if bearish:
        return "put"

    return None


# =========================================================
# 📊 MICROESTRUCTURA (5s)
# =========================================================

def get_ticks(df_5s):
    return df_5s.tail(12)


def micro_analysis(ticks):

    up = 0
    down = 0
    rejections = 0

    for i in range(len(ticks)):
        o = ticks.iloc[i]["open"]
        c = ticks.iloc[i]["close"]
        h = ticks.iloc[i]["high"]
        l = ticks.iloc[i]["low"]

        body = abs(c - o)
        wick = (h - l) - body

        if c > o:
            up += 1
        else:
            down += 1

        if wick > body:
            rejections += 1

    return up, down, rejections


# =========================================================
# 🧠 TRAMPA (MANIPULACIÓN)
# =========================================================

def detect_trap(ticks):

    last = ticks.iloc[-1]
    prev = ticks.iloc[-2]

    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return "put"

    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return "call"

    return None


# =========================================================
# 🎯 SCORE
# =========================================================

def build_score(direction, ticks, mem, aggressive=False):

    up, down, rejections = micro_analysis(ticks)

    score = 0

    # dominancia
    if direction == "call" and up > down:
        score += 30

    if direction == "put" and down > up:
        score += 30

    # rechazo institucional
    if rejections >= 3:
        score += 20

    # movimiento
    move = ticks.iloc[-1]["close"] - ticks.iloc[0]["open"]

    if direction == "call" and move > 0:
        score += 20

    if direction == "put" and move < 0:
        score += 20

    # IA
    score *= mem["confidence"]

    # 🔥 modo agresivo
    if aggressive:
        score += 10

    return score


# =========================================================
# 🚀 SEÑAL PRINCIPAL
# =========================================================

def pro_signal(df_m1, df_5s, aggressive=False):

    mem = load_memory()

    if df_m1 is None or df_5s is None:
        return None, None

    if len(df_m1) < 20 or len(df_5s) < 20:
        return None, None

    # =============================
    # CONTEXTO
    # =============================
    direction = get_context(df_m1)

    if direction is None:
        return None, None

    ticks = get_ticks(df_5s)

    # =============================
    # TRAMPA
    # =============================
    trap = detect_trap(ticks)
    if trap:
        direction = trap

    # =============================
    # SCORE
    # =============================
    score = build_score(direction, ticks, mem, aggressive)

    # 🎯 umbral dinámico
    threshold = 50 if not aggressive else 35

    if score < threshold:
        return None, None

    # =============================
    # FILTROS PRO
    # =============================
    last = df_m1.iloc[-1]

    body = abs(last["close"] - last["open"])
    avg = (df_m1["high"] - df_m1["low"]).tail(10).mean()

    # evitar velas FOMO
    if body > avg * 1.7:
        return None, None

    price = last["close"]
    high = df_m1["high"].tail(10).max()
    low = df_m1["low"].tail(10).min()

    # evitar extremos
    if direction == "call" and abs(price - high) < 0.00015:
        return None, None

    if direction == "put" and abs(price - low) < 0.00015:
        return None, None

    return direction, score


# =========================================================
# 🧠 ACTUALIZAR IA (IMPORTANTE)
# =========================================================

def update_result(result):

    mem = load_memory()

    if result == 1:
        mem["wins"] += 1
        mem["confidence"] *= 1.02
    else:
        mem["losses"] += 1
        mem["confidence"] *= 0.98

    # límites
    mem["confidence"] = max(0.5, min(2.0, mem["confidence"]))

    save_memory(mem)
