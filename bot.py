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

AMOUNT = 20000
EXPIRATION = 1  # 1 minuto

# ==============================
# VARIABLES
# ==============================
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
print("🔌 Conectando a IQ Option...", flush=True)

Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error de conexión", flush=True)
    exit()

print("✅ Conectado", flush=True)
send_telegram("🤖 BOT SNIPER ACTIVADO")

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
        # NUEVA VELA DETECTADA
        # ==============================
        if last_candle_time != current_time:

            print("🟢 Nueva vela", flush=True)

            # ==============================
            # EJECUTAR SEÑAL PENDIENTE
            # ==============================
            if pending_signal is not None:

                direccion = pending_signal["direction"]

                print(f"🚀 ENTRADA SNIPER → {direccion}", flush=True)

                status, trade_id = Iq.buy(AMOUNT, PAIR, direccion, EXPIRATION)

                if status:
                    send_telegram(
                        f"🚀 SNIPER ENTRY\n"
                        f"{PAIR} → {direccion.upper()}"
                    )

                    # esperar resultado
                    time.sleep(EXPIRATION * 60)

                    result = Iq.check_win_v4(trade_id)

                    # FIX errores tuple/string
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
                    print("❌ No ejecutó operación", flush=True)

                # limpiar señal
                pending_signal = None

            # ==============================
            # ANALIZAR VELA QUE CERRÓ
            # ==============================
            signal = pro_signal(df)

            if signal is not None:

                direccion = signal.get("direction")

                # 🔥 PROTECCIÓN ERROR None.upper()
                if direccion is None:
                    last_candle_time = current_time
                    continue

                score = signal.get("score", 0)
                reason = signal.get("reason", [])

                print(f"🔥 Señal detectada → {direccion}", flush=True)

                # GUARDAR PARA SIGUIENTE VELA
                pending_signal = signal

                send_telegram(
                    f"📊 SEÑAL DETECTADA\n"
                    f"{PAIR}\n"
                    f"{direccion.upper()}\n"
                    f"Score: {score}\n"
                    f"Entrada en próxima vela"
                )

            last_candle_time = current_time

        # velocidad optimizada
        time.sleep(0.3)

    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}", flush=True)
        time.sleep(2)
