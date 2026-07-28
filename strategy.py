import numpy as np
from datetime import datetime

# ================= INDICADORES (NO SE USAN PERO SE MANTIENE POR TU BOT) =================

def add_indicators(df):
    return df


# ================= DETECTAR PATRÓN =================

def detect_trendline_pattern(df):

    c1 = df.iloc[-3]
    c2 = df.iloc[-2]
    c3 = df.iloc[-1]

    # ================= COMPRA =================
    if (
        c1["close"] > c1["open"] and
        c2["close"] > c2["open"] and
        c3["close"] > c3["open"]
    ):

        low1 = c1["low"]
        low2 = c2["low"]

        if low1 < low2:
            return "call", low1, low2, -3, -2

    # ================= VENTA =================
    if (
        c1["close"] < c1["open"] and
        c2["close"] < c2["open"] and
        c3["close"] < c3["open"]
    ):

        high1 = c1["high"]
        high2 = c2["high"]

        if high1 > high2:
            return "put", high1, high2, -3, -2

    return None, None, None, None, None


# ================= PROYECTAR LÍNEA =================

def project_line(p1, p2, i1, i2, current_index):

    slope = (p2 - p1) / (i2 - i1)
    projected = p2 + slope * (current_index - i2)

    return projected


# ================= TOQUE EN M1 =================

def touch_line(df_m1, line_price):

    last = df_m1.iloc[-1]

    return last["low"] <= line_price <= last["high"]


# ================= TIEMPO EXPIRACIÓN =================

def time_to_close_m5(timestamp):

    dt = datetime.fromtimestamp(timestamp)
    minute = dt.minute

    remaining = 5 - (minute % 5)

    return remaining


# ================= FUNCIÓN PRINCIPAL =================

def pro_signal(df_m1, df_m5, df_htf):

    # timestamp actual (usamos última vela M1)
    current_timestamp = df_m1["from"].iloc[-1]

    direction, p1, p2, i1, i2 = detect_trendline_pattern(df_m5)

    if direction is None:
        return None, None

    current_index = len(df_m5) - 1
    price = df_m5["close"].iloc[-1]

    line_price = project_line(p1, p2, i1, i2, current_index)

    # ================= COMPRA =================
    if direction == "call":

        # precio debe estar arriba
        if price <= line_price:
            return None, None

        # esperar toque en M1
        if touch_line(df_m1, line_price):

            expiration = time_to_close_m5(current_timestamp)
            return "call", expiration

    # ================= VENTA =================
    if direction == "put":

        # precio debe estar abajo
        if price >= line_price:
            return None, None

        if touch_line(df_m1, line_price):

            expiration = time_to_close_m5(current_timestamp)
            return "put", expiration

    return None, None
