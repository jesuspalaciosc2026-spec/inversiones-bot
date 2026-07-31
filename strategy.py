import numpy as np

# ================= MICRO FLOW =================

def micro_flow(df):
    closes = df["close"].values

    up_moves = 0
    down_moves = 0
    rejections = 0
    strength = 0

    for i in range(1, len(closes)):

        diff = closes[i] - closes[i - 1]

        # conteo de dirección
        if diff > 0:
            up_moves += 1
        elif diff < 0:
            down_moves += 1

        # rechazo (cambio de dirección)
        if i > 1:
            prev = closes[i - 1] - closes[i - 2]
            if prev * diff < 0:
                rejections += 1

        strength += abs(diff)

    total = len(closes)

    dominance = abs(up_moves - down_moves) / total if total > 0 else 0
    avg_strength = strength / total if total > 0 else 0

    direction = "call" if up_moves >= down_moves else "put"

    return {
        "direction": direction,
        "dominance": dominance,
        "rejections": rejections,
        "strength": avg_strength,
        "up": up_moves,
        "down": down_moves
    }


# ================= CLASIFICACIÓN =================

def classify(flow):

    # tendencia clara → continuación
    if flow["dominance"] > 0.55 and flow["rejections"] <= 3:
        return "continuation"

    # mucha indecisión → posible reversión
    if flow["rejections"] >= 4:
        return "reversal"

    return "neutral"


# ================= SCORE =================

def score_flow(flow):

    score = 0

    if flow["dominance"] > 0.6:
        score += 2
    elif flow["dominance"] > 0.5:
        score += 1

    if flow["rejections"] <= 2:
        score += 2
    elif flow["rejections"] <= 4:
        score += 1

    if flow["strength"] > 0:
        score += 1

    return score


# ================= DECISIÓN =================

def decide(flow):

    setup = classify(flow)
    score = score_flow(flow)

    # CONTINUACIÓN
    if setup == "continuation":
        return flow["direction"], score

    # REVERSIÓN
    if setup == "reversal":
        opposite = "put" if flow["direction"] == "call" else "call"
        return opposite, score

    # NEUTRAL → igual entra (para no bloquear el bot)
    return flow["direction"], score


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1):

    if df_m1 is None or len(df_m1) < 10:
        return None, None

    flow = micro_flow(df_m1)

    direction, score = decide(flow)

    # 🔥 SIEMPRE OPERA (como pediste)
    return direction, 1
