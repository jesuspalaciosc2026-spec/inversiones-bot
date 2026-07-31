import numpy as np

# ================= MICRO FLOW =================

def micro_flow(df_1s):
    closes = df_1s["close"].values

    up_moves = 0
    down_moves = 0
    rejections = 0
    speed = 0

    for i in range(1, len(closes)):

        diff = closes[i] - closes[i-1]

        if diff > 0:
            up_moves += 1
        elif diff < 0:
            down_moves += 1

        # cambios de dirección (rechazos)
        if i > 1:
            prev_diff = closes[i-1] - closes[i-2]
            if prev_diff * diff < 0:
                rejections += 1

        speed += abs(diff)

    total = len(closes)

    dominance = abs(up_moves - down_moves) / total if total > 0 else 0
    volatility = np.std(closes)
    avg_speed = speed / total if total > 0 else 0

    direction = "call" if up_moves >= down_moves else "put"

    return {
        "direction": direction,
        "dominance": dominance,
        "rejections": rejections,
        "volatility": volatility,
        "speed": avg_speed,
        "up": up_moves,
        "down": down_moves
    }

# ================= CLASIFICACIÓN =================

def classify(flow):

    # 🔥 CONTINUACIÓN (flujo limpio)
    if flow["dominance"] > 0.55 and flow["rejections"] <= 3:
        return "continuation"

    # 🔁 REVERSIÓN (mucho rechazo)
    if flow["rejections"] >= 4:
        return "reversal"

    return "neutral"

# ================= SCORE =================

def score_flow(flow):

    score = 0

    # dominancia
    if flow["dominance"] > 0.6:
        score += 2
    elif flow["dominance"] > 0.5:
        score += 1

    # pocos rechazos
    if flow["rejections"] <= 2:
        score += 2
    elif flow["rejections"] <= 4:
        score += 1

    # velocidad
    if flow["speed"] > 0:
        score += 1

    return score

# ================= DECISIÓN =================

def decide(flow):

    setup = classify(flow)
    score = score_flow(flow)

    # 🔥 SIEMPRE DEVUELVE DIRECCIÓN (para que opere)
    if setup == "continuation":
        return flow["direction"], score

    if setup == "reversal":
        opposite = "put" if flow["direction"] == "call" else "call"
        return opposite, score

    # neutral → igual entra (forzado)
    return flow["direction"], score

# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1, df_m5, df_1s):

    if df_1s is None or len(df_1s) < 10:
        return None, None

    flow = micro_flow(df_1s)

    direction, score = decide(flow)

    # puedes usar el score si quieres filtrar en el futuro
    # ahora NO bloquea para que siempre opere

    return direction, 1
