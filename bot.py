import os
import time
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal, update_result

# ==============================
# CONFIGURACIÓN
# ==============================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIR = "EURUSD-OTC"

AMOUNT = 35
EXPIRATION = 1

bot_active = True
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
    except Exception as e:
        print(f"❌ Error Telegram: {e}", flush=True)


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
send_telegram("🤖 BOT SNIPER ACTIVO")

# ==============================
# LOOP PRINCIPAL
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
        seconds = int(time.time()) % 60

        # ==============================
        # NUEVA VELA DETECTADA
        # ==============================
        if last_candle_time != current_time:

            last_candle_time = current_time
            print("🟢 Nueva vela detectada", flush=True)

            # Analizar vela cerrada
            try:
                signal = pro_signal(df)

                if signal is not None:
                    direccion, patron, score = signal

                    pending_signal = direccion

                    print(f"🔥 Señal detectada: {direccion}", flush=True)

                    send_telegram(
                        f"📊 EURUSD-OTC\n"
                        f"Señal: {direccion.upper()}\n"
                        f"Modo: SNIPER\n"
                        f"Entrada en siguiente vela"
                    )

                else:
                    pending_signal = None

            except Exception as e:
                print(f"❌ Error análisis: {e}", flush=True)

        # ==============================
        # ENTRADA SNIPER (SEGUNDO 59)
        # ==============================
        if pending_signal is not None and seconds == 59:

            print("🎯 Ejecutando entrada SNIPER...", flush=True)

            direccion = pending_signal
            pending_signal = None

            status, trade_id = Iq.buy(AMOUNT, PAIR, direccion, EXPIRATION)

            if status:
                print("✅ OPERACIÓN ABIERTA", flush=True)

                send_telegram(
                    f"🚀 ENTRADA SNIPER\n"
                    f"{PAIR} → {direccion.upper()}"
                )

                time.sleep(EXPIRATION * 60)

                result = Iq.check_win_v4(trade_id)

                # 🔥 FIX errores tuple
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
                print("❌ No se ejecutó la orden", flush=True)

        time.sleep(0.5)

    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}", flush=True)
        time.sleep(2)
