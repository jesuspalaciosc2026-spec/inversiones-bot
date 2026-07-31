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
        "up_moves": up_moves,
        "down_moves": down_moves,
        "rejections": rejections,
        "dominance": dominance,
        "volatility": volatility
    }

# ================= CLASIFICACIÓN =================

def classify_flow(flow):

    # continuación fuerte
    if flow["dominance"] > 0.6 and flow["rejections"] < 3:
        return "continuation"

    # reversión
    if flow["rejections"] >= 4 and flow["dominance"] < 0.4:
        return "reversal"

    return None

# ================= FILTROS =================

def strong_flow(flow):
    return flow["volatility"] > 0 and flow["dominance"] > 0.5


def not_noise(df_1s):
    closes = df_1s["close"].values

    if len(closes) < 10:
        return False

    movement = abs(closes[-1] - closes[0])
    noise = np.std(closes)

    return movement > noise * 0.5

# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1, df_m5, df_1s):

    if df_1s is None or len(df_1s) < 20:
        return None, None

    if not not_noise(df_1s):
        return None, None

    flow = micro_flow(df_1s)

    if not strong_flow(flow):
        return None, None

    setup = classify_flow(flow)

    if setup is None:
        return None, None

    # continuación
    if setup == "continuation":
        return flow["direction"], 1

    # reversión
    if setup == "reversal":
        opposite = "put" if flow["direction"] == "call" else "call"
        return opposite, 1

    return None, None
