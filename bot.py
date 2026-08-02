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
AMOUNT = 1000            # monto de entrada
EXPIRATION = 1        # 1 minuto (tu preferido)

# =========================
# 🔌 CONEXIÓN IQ OPTION
# =========================
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conectando a IQ Option")
    exit()
else:
    print("✅ Conectado a IQ Option")

# =========================
# 🧠 CONTROL DE OPERACIONES
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

        current_time = df["from"].iloc[-1]

        # evitar repetir vela
        if last_candle_time == current_time:
            time.sleep(1)
            continue

        last_candle_time = current_time

        signal = generate_signal(df)

        if signal and not trade_open:

            direction = signal["direction"]
            score = signal["score"]

            print(f"\n📊 SEÑAL DETECTADA")
            print(f"👉 Dirección: {direction}")
            print(f"⭐ Score: {score}")

            # ejecutar operación
            check, trade_id = Iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

            if check:
                print("✅ OPERACIÓN EJECUTADA")

                trade_open = True

                # esperar resultado
                time.sleep(EXPIRATION * 60)

                trade_open = False
                print("⏳ Esperando nueva oportunidad...\n")

            else:
                print("❌ Error al ejecutar operación")

        time.sleep(2)

    except Exception as e:
        print("⚠ ERROR:", e)
        time.sleep(5)
