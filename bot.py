import os
import time
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal, update_result

# ==============================
# CONFIG
# ==============================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIR = "EURUSD-OTC"

AMOUNT = 75
EXPIRATION = 1

last_candle_time = None
pending_signal = None

# ==============================
# TELEGRAM
# ==============================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        })
    except:
        pass

# ==============================
# CONEXIÓN
# ==============================
print("🔌 Conectando...", flush=True)
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conexión", flush=True)
    exit()

print("✅ Conectado", flush=True)
send_telegram("🤖 BOT CONTINUIDAD ACTIVO")

# ==============================
# LOOP
# ==============================
while True:
    try:
        candles = Iq.get_candles(PAIR, 60, 100, time.time())

        if not candles:
            time.sleep(1)
            continue

        df = pd.DataFrame([{
            "open": c["open"],
            "close": c["close"],
            "max": c["max"],
            "min": c["min"]
        } for c in candles])

        current_time = candles[-1]["from"]

        # ==============================
        # NUEVA VELA = MOMENTO DE ENTRADA
        # ==============================
        if last_candle_time is not None and current_time != last_candle_time:

            print("🟢 Nueva vela abierta", flush=True)

            # 🚀 EJECUTAR SI HABÍA SEÑAL
            if pending_signal is not None:

                direccion = pending_signal
                pending_signal = None

                print(f"🎯 ENTRANDO: {direccion}", flush=True)

                send_telegram(
                    f"🚀 ENTRADA\n"
                    f"{PAIR} → {direccion.upper()}"
                )

                status, trade_id = Iq.buy(AMOUNT, PAIR, direccion, EXPIRATION)

                if status:

                    time.sleep(EXPIRATION * 60)

                    result = Iq.check_win_v4(trade_id)

                    # FIX tuple
                    if isinstance(result, tuple):
                        result = result[0]

                    try:
                        result = float(result)
                    except:
                        result = 0

                    update_result(result)

                    print(f"📈 Resultado: {result}", flush=True)
                    send_telegram(f"📈 Resultado: {result}")

                else:
                    print("❌ Error al ejecutar", flush=True)

        # ==============================
        # DETECTAR SEÑAL EN VELA CERRADA
        # ==============================
        if last_candle_time != current_time:

            last_candle_time = current_time

            try:
                signal = pro_signal(df)

                if signal is not None:

                    direccion, patron, score = signal

                    pending_signal = direccion

                    print(f"🔥 Señal detectada: {direccion}", flush=True)

                    send_telegram(
                        f"📊 EURUSD-OTC\n"
                        f"Señal: {direccion.upper()}\n"
                        f"Entrada: siguiente vela"
                    )

                else:
                    pending_signal = None

            except Exception as e:
                print(f"❌ Error señal: {e}", flush=True)

        time.sleep(0.5)

    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}", flush=True)
        time.sleep(2)
