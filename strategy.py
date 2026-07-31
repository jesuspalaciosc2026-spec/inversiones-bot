import numpy as np
from datetime import datetime

# ================= LATERALIDAD / TENDENCIA SUAVE =================

def is_valid_structure(df):

    recent = df.tail(20)

    highs = recent["high"]
    lows = recent["low"]

    # estructura limpia (sin caos)
    return (highs.max() - lows.min()) > (highs - lows).mean() * 3


# ================= DETECTAR LÍNEA =================

def detect_trendline(df):

    lows = df["low"].values
    highs = df["high"].values

    touches = []

    for i in range(len(df)-10, len(df)):
        for j in range(i+1, len(df)):
            if lows[i] < lows[j]:
                touches.append((i, j, lows[i], lows[j]))

    if len(touches) < 1:
        return None

    i1, i2, p1, p2 = touches[-1]

    return "call", p1, p2, i1, i2


# ================= FIBONACCI =================

def fibonacci_zone(df):

    recent = df.tail(20)

    high = recent["high"].max()
    low = recent["low"].min()

    fib_50 = high - (high - low) * 0.5
    fib_618 = high - (high - low) * 0.618

    return fib_50, fib_618


# ================= PROYECTAR LÍNEA =================

def project_line(p1, p2, i1, i2, current_index):

    slope = (p2 - p1) / (i2 - i1)
    return p2 + slope * (current_index - i2)


# ================= RETEST REAL =================

def valid_retest(df_m1, line_price):

    prev = df_m1.iloc[-2]
    last = df_m1.iloc[-1]

    # estaba lejos
    was_far = abs(prev["close"] - line_price) > (prev["high"] - prev["low"])

    # toca línea
    touch = last["low"] <= line_price <= last["high"]

    return was_far and touch


# ================= EXPIRACIÓN =================

def time_to_close_m5(timestamp):

    dt = datetime.fromtimestamp(timestamp)
    minute = dt.minute

    return 5 - (minute % 5)


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1, df_m5, df_htf):

    # 1. ESTRUCTURA
    if not is_valid_structure(df_m5):
        return None, None

    # 2. LÍNEA
    result = detect_trendline(df_m5)

    if result is None:
        return None, None

    direction, p1, p2, i1, i2 = result

    current_index = len(df_m5) - 1
    line_price = project_line(p1, p2, i1, i2, current_index)

    price = df_m5["close"].iloc[-1]

    # 3. FIBONACCI
    fib_50, fib_618 = fibonacci_zone(df_m5)

    in_fib_zone = fib_618 <= price <= fib_50

    if not in_fib_zone:
        return None, None

    # 4. RETEST
    if not valid_retest(df_m1, line_price):
        return None, None

    # 5. EXPIRACIÓN
    timestamp = df_m1["from"].iloc[-1]
    expiration = time_to_close_m5(timestamp)

    return "call", expiration
