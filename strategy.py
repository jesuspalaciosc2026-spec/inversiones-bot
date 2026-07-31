import numpy as np

# ================= MICRO FLOW =================

def micro_flow(df_1s):

    closes = df_1s["close"].values

    up_moves = 0
    down_moves = 0
    rejections = 0

    for i in range(1, len(closes)):

        if closes[i] > closes[i-1]:
            up_moves += 1
        elif closes[i] < closes[i-1]:
            down_moves += 1

        # cambio de dirección = rechazo
        if i > 1:
            prev = closes[i-1] - closes[i-2]
            curr = closes[i] - closes[i-1]

            if prev * curr < 0:
                rejections += 1

    total = len(closes)

    dominance = abs(up_moves - down_moves) / total if total > 0 else 0
    volatility = np.std(closes)

    direction = "call" if up_moves > down_moves else "put"

    return {
        "direction": direction,
        "dominance": dominance,
        "rejections": rejections,
        "volatility": volatility
    }

# ================= CLASIFICACIÓN =================

def classify_flow(flow):

    # 🔥 continuación (más flexible)
    if flow["dominance"] > 0.52 and flow["rejections"] <= 4:
        return "continuation"

    # 🔁 reversión (más flexible)
    if flow["rejections"] >= 3 and flow["dominance"] < 0.48:
        return "reversal"

    return None

# ================= FILTRO SUAVE =================

def strong_flow(flow):
    return flow["dominance"] > 0.48

# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1, df_m5, df_1s):

    if df_1s is None or len(df_1s) < 20:
        return None, None

    flow = micro_flow(df_1s)

    if not strong_flow(flow):
        return None, None

    setup = classify_flow(flow)

    if setup is None:
        return None, None

    # CONTINUACIÓN
    if setup == "continuation":
        return flow["direction"], 1

    # REVERSIÓN
    if setup == "reversal":
        opposite = "put" if flow["direction"] == "call" else "call"
        return opposite, 1

    return None, None
