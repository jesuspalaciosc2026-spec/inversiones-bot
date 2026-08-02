import time
import os
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import generate_signal

# =========================
# 🔐 VARIABLES DE ENTORNO
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

# =========================
# ⚙ CONFIGURACIÓN
# =========================
PAIR = "EURUSD-OTC"   # puedes cambiarlo
AMOUNT = 2000            # monto por operación
EXPIRATION = 1        # 1 minuto

# =========================
# 🔌 CONEXIÓN
# =========================
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conectando a IQ Option")
    exit()
else:
    print("✅ Conectado correctamente")

# =========================
# 🧠 CONTROL
# =========================
trade_open = False
last_candle_time = None


# =========================
# 📊 OBTENER VELAS
# =========================
def get_candles():
    candles = Iq.get_candles(PAIR, 60, 50, time.time())

    df = pd.DataFrame(candles)

    df.rename(columns={
        "min": "low",
        "max": "high"
    }, inplace=True)

    return df


# =========================
# 🚀 LOOP PRINCIPAL
# =========================
while True:
    try:
        df = get_candles()

        if df is None or len(df) == 0:
            time.sleep(2)
            continue

        current_time = df["from"].iloc[-1]

        # evitar repetir la misma vela
        if last_candle_time == current_time:
            time.sleep(1)
            continue

        last_candle_time = current_time

        # =========================
        # 📊 GENERAR SEÑAL
        # =========================
        signal = generate_signal(df)

        if signal and not trade_open:

            direction = signal["direction"]
            score = signal["score"]

            print("\n📊 NUEVA SEÑAL DETECTADA")
            print(f"👉 Dirección: {direction}")
            print(f"⭐ Score: {score}")

            # =========================
            # 🚀 EJECUTAR OPERACIÓN
            # =========================
            check, trade_id = Iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

            if check:
                print("✅ OPERACIÓN ABIERTA")

                trade_open = True

                # esperar resultado
                time.sleep(EXPIRATION * 60)

                trade_open = False
                print("⏳ Esperando siguiente oportunidad...\n")

            else:
                print("❌ Error al ejecutar operación")

        # =========================
        # ⏱ PAUSA
        # =========================
        time.sleep(2)

    except Exception as e:
        print("⚠ ERROR GENERAL:", e)
        time.sleep(5)
