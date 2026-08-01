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
                "trap_put": 0,
                "aggressive": 0
            },
            "confidence": {
                "trend_call": 1.0,
                "trend_put": 1.0,
                "trap_call": 1.0,
                "trap_put": 1.0,
                "aggressive": 1.0
            }
        }

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(mem):
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f)


# =========================================================
# 📊 CONTEXTO
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
# ⚡ MICROESTRUCTURA
# =========================================================

def micro_analysis(df):
    up = sum(1 for i in range(len(df)) if df.iloc[i]["close"] > df.iloc[i]["open"])
    down = sum(1 for i in range(len(df)) if df.iloc[i]["close"] < df.iloc[i]["open"])

    return up, down


# =========================================================
# 🎯 PRO SIGNAL
# =========================================================

def pro_signal(df_m1, df_5s, aggressive=False):

    mem = load_memory()

    # ❗ SIEMPRE 3 VALORES
    if df_m1 is None or df_5s is None:
        return None, None, None

    if len(df_m1) < 10 or len(df_5s) < 10:
        return None, None, None

    direction = get_context(df_m1)

    if direction is None:
        return None, None, None

    ticks = df_5s.tail(10)
    up, down = micro_analysis(ticks)

    score = 0

    if direction == "call" and up > down:
        score += 40

    if direction == "put" and down > up:
        score += 40

    # IA aprendizaje
    confidence = mem["confidence"].get("aggressive", 1.0)
    score *= confidence

    # 🔥 MODO AGRESIVO
    threshold = 50
    if aggressive:
        threshold = 20

    if score < threshold:
        return None, None, None

    # evitar velas locas
    last = df_m1.iloc[-1]
    body = abs(last["close"] - last["open"])
    avg = (df_m1["high"] - df_m1["low"]).tail(10).mean()

    if body > avg * 1.5:
        return None, None, None

    return direction, 1, "aggressive"


# =========================================================
# 🧠 ACTUALIZAR IA
# =========================================================

def update_result(result, pattern):

    mem = load_memory()

    if pattern not in mem["confidence"]:
        mem["confidence"][pattern] = 1.0
        mem["patterns"][pattern] = 0

    if result == 1:
        mem["wins"] += 1
        mem["patterns"][pattern] += 1
        mem["confidence"][pattern] *= 1.05
    else:
        mem["losses"] += 1
        mem["confidence"][pattern] *= 0.95

    mem["confidence"][pattern] = max(0.5, min(2.0, mem["confidence"][pattern]))

    save_memory(mem)
