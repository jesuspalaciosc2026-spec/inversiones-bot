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
            "patterns": {
                "trend_call": 0,
                "trend_put": 0,
                "trap_call": 0,
                "trap_put": 0
            },
            "confidence": {
                "trend_call": 1.0,
                "trend_put": 1.0,
                "trap_call": 1.0,
                "trap_put": 1.0
            }
        }

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f)


# =========================================================
# 🧠 CONTEXTO (M1) MÁS FLEXIBLE
# =========================================================

def get_context(df):

    highs = df["high"].tail(3).values
    lows = df["low"].tail(3).values

    bullish = highs[-1] > highs[-2] and lows[-1] > lows[-2]
    bearish = highs[-1] < highs[-2] and lows[-1] < lows[-2]

    if bullish:
        return "call"

    if bearish:
        return "put"

    return None


# =========================================================
# 📊 MICROESTRUCTURA
# =========================================================

def get_ticks(df):
    return df.tail(10)


def micro_analysis(ticks):

    up, down = 0, 0

    for i in range(len(ticks)):
        if ticks.iloc[i]["close"] > ticks.iloc[i]["open"]:
            up += 1
        else:
            down += 1

    return up, down


# =========================================================
# 🧠 TRAMPA
# =========================================================

def detect_trap(ticks):

    last = ticks.iloc[-1]
    prev = ticks.iloc[-2]

    if last["high"] > prev["high"] and last["close"] < prev["close"]:
        return "put"

    if last["low"] < prev["low"] and last["close"] > prev["close"]:
        return "call"

    return None


# =========================================================
# 🎯 SCORE MÁS AGRESIVO
# =========================================================

def build_score(direction, ticks, mem):

    up, down = micro_analysis(ticks)

    score = 0

    if direction == "call" and up >= down:
        score += 20

    if direction == "put" and down >= up:
        score += 20

    move = ticks.iloc[-1]["close"] - ticks.iloc[0]["open"]

    if direction == "call" and move > 0:
        score += 15

    if direction == "put" and move < 0:
        score += 15

    return score


# =========================================================
# 🚀 SEÑAL AGRESIVA
# =========================================================

def pro_signal(df_m1, df_micro):

    if df_m1 is None or df_micro is None:
        return None, None, None

    direction = get_context(df_m1)

    if direction is None:
        return None, None, None

    ticks = get_ticks(df_micro)

    trap = detect_trap(ticks)
    if trap:
        direction = trap

    score = build_score(direction, ticks, None)

    print(f"🔥 AGRESIVO → score: {score} | dir: {direction}")

    # 🔥 UMBRAL MUY BAJO
    if score < 15:
        return None, None, None

    return direction, 1, "aggressive"


# =========================================================
# 🧠 IA
# =========================================================

def update_result(result, pattern):

    mem = load_memory()

    if result == 1:
        mem["wins"] += 1
    else:
        mem["losses"] += 1

    save_memory(mem)
