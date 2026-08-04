import os
import time
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal

# =========================
# CONFIG
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

PAIR = "EURUSD-OTC"
AMOUNT = 55
EXPIRATION = 1

# =========================
# CONEXIÓN
# =========================
def conectar():
    print("🔌 Conectando...")
    iq = IQ_Option(EMAIL, PASSWORD)
    status, reason = iq.connect()

    if not status:
        print("❌ ERROR:", reason)
        return None

    print("✅ Conectado")
    iq.change_balance("PRACTICE")
    return iq


iq = conectar()
if iq is None:
    exit()

# =========================
# CONTROL
# =========================
last_candle_time = None
operacion_ejecutada = False

# =========================
# LOOP
# =========================
while True:
    try:
        # 🔄 RECONEXIÓN
        if not iq.check_connect():
            print("🔁 Reconectando...")
            iq = conectar()
            time.sleep(3)
            continue

        candles = iq.get_candles(PAIR, 60, 100, time.time())

        if not candles:
            time.sleep(1)
            continue

        # 🔥 CONVERTIR A DATAFRAME (SOLUCION IL0C)
        df = pd.DataFrame(candles)

        current_candle_time = df.iloc[-1]["from"]

        # =========================
        # NUEVA VELA
        # =========================
        if last_candle_time != current_candle_time:
            last_candle_time = current_candle_time
            operacion_ejecutada = False

            print("🟢 Nueva vela")

            # =========================
            # ANALIZAR
            # =========================
            signal = pro_signal(df)

            if signal and not operacion_ejecutada:
                print(f"🔥 SEÑAL: {signal.upper()}")

                # =========================
                # EJECUTAR EN APERTURA
                # =========================
                status, trade_id = iq.buy(AMOUNT, PAIR, signal, EXPIRATION)

                if status:
                    print(f"✅ ENTRADA → {signal.upper()}")
                    operacion_ejecutada = True
                else:
                    print("❌ Error al ejecutar")

        time.sleep(1)

    except Exception as e:
        print("❌ ERROR GENERAL:", e)
        time.sleep(3)
