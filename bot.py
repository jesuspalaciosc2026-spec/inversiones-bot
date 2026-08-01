import time
import os
import logging
from iqoptionapi.stable_api import IQ_Option

from strategy import pro_signal, update_result

# =========================================================
# ⚙️ CONFIG
# =========================================================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

PAIRS = ["EURUSD", "GBPUSD", "EURJPY", "EURGBP", "USDCHF"]
AMOUNT = 20000
EXPIRATION = 1  # 1 minuto

# =========================================================
# 🔇 LOGS OFF
# =========================================================

logging.getLogger().setLevel(logging.CRITICAL)

# =========================================================
# 🔌 CONEXIÓN
# =========================================================

print("🔌 Conectando a IQ Option...")
iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error de conexión")
    exit()

print("✅ Conectado correctamente")

# =========================================================
# 📊 DATA
# =========================================================

def get_candles(pair, timeframe, count):
    candles = iq.get_candles(pair, timeframe, count, time.time())
    if candles is None:
        return None

    import pandas as pd
    df = pd.DataFrame(candles)

    df.rename(columns={
        "max": "high",
        "min": "low"
    }, inplace=True)

    return df

# =========================================================
# 💰 RESULTADO REAL
# =========================================================

def check_result(order_id):

    while True:
        check, win = iq.check_win_v4(order_id)

        if check:
            if win > 0:
                return 1  # WIN
            else:
                return 0  # LOSS

        time.sleep(1)

# =========================================================
# 🚀 BOT LOOP
# =========================================================

trade_open = False
last_trade_time = 0

while True:
    try:

        if trade_open:
            time.sleep(1)
            continue

        for pair in PAIRS:

            # =========================
            # 📊 DATOS
            # =========================
            df_m1 = get_candles(pair, 60, 50)
            df_5s = get_candles(pair, 5, 50)

            if df_m1 is None or df_5s is None:
                continue

            # =========================
            # 🧠 SEÑAL IA
            # =========================
            signal, expiration, pattern = pro_signal(df_m1, df_5s)

            if signal is None:
                continue

            # evitar overtrading
            if time.time() - last_trade_time < 60:
                continue

            print(f"🎯 SEÑAL {pair} → {signal.upper()} | patrón: {pattern}")

            # =========================
            # 💸 ENTRADA
            # =========================
            status, order_id = iq.buy(
                AMOUNT,
                pair,
                signal,
                expiration
            )

            if status:
                print("✅ OPERACIÓN ABIERTA")
                trade_open = True
                last_trade_time = time.time()

                # =========================
                # 🧾 RESULTADO
                # =========================
                result = check_result(order_id)

                if result == 1:
                    print("🏆 WIN")
                else:
                    print("❌ LOSS")

                # =========================
                # 🧠 IA APRENDE
                # =========================
                update_result(result, pattern)

                trade_open = False

            else:
                print("❌ Error al abrir operación")

        time.sleep(1)

    except Exception as e:
        print("⚠️ ERROR:", e)
        time.sleep(5)
