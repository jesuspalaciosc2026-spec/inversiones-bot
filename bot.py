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

PAIRS = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC"
]

AMOUNT = 20000
EXPIRATION = 1

last_candle_time = {}

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
        print("Telegram error:", e)


# ==============================
# ⏳ ESPERA SEGUNDO 59
# ==============================
def esperar_segundo_59():
    while True:
        now = time.localtime()
        if now.tm_sec >= 59:
            break
        time.sleep(0.2)


# ==============================
# CONEXIÓN
# ==============================
print("🔌 Conectando...")
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conexión")
    exit()

print("✅ Conectado")
send_telegram("🤖 BOT INICIADO")

# ==============================
# LOOP PRINCIPAL
# ==============================
while True:
    try:
        for pair in PAIRS:

            candles = Iq.get_candles(pair, 60, 100, time.time())

            if not candles:
                continue

            # 🔥 DATA LIMPIA
            df = pd.DataFrame([{
                "open": float(c["open"]),
                "close": float(c["close"]),
                "max": float(c["max"]),
                "min": float(c["min"])
            } for c in candles])

            current_time = candles[-1]["from"]

            # 🚫 EVITAR REPETIR EN MISMA VELA
            if pair in last_candle_time and last_candle_time[pair] == current_time:
                continue

            signal = pro_signal(df)

            if not signal:
                continue

            direccion = signal["direction"]
            score = signal.get("score", 0)
            reason = signal.get("reason", [])

            print(f"🔥 SEÑAL {pair}: {direccion}")

            # ⏳ ESPERA SNIPER
            esperar_segundo_59()

            # 🔒 BLOQUEAR ESTA VELA
            last_candle_time[pair] = current_time

            # 🚀 ENTRADA
            status, trade_id = Iq.buy(AMOUNT, pair, direccion, EXPIRATION)

            if status:
                print("✅ OPERACIÓN ABIERTA")

                send_telegram(
                    f"📊 {pair}\n"
                    f"Dirección: {direccion.upper()}\n"
                    f"Score: {score}\n"
                    f"Motivo:\n- " + "\n- ".join(reason)
                )

                # ⏳ ESPERAR RESULTADO
                time.sleep(EXPIRATION * 60)

                result = Iq.check_win_v4(trade_id)

                # 🔥 NORMALIZAR RESULTADO
                if isinstance(result, tuple):
                    result = result[0]

                if isinstance(result, str):
                    if result.lower() == "win":
                        result = 1
                    elif result.lower() == "loose":
                        result = -1
                    else:
                        result = 0

                update_result(result)

                send_telegram(f"📈 Resultado: {result}")

                # 🔥 SOLO 1 TRADE POR CICLO
                break

            else:
                print("❌ Error al abrir operación")

        time.sleep(1)

    except Exception as e:
        print("❌ ERROR GENERAL:", e)
        time.sleep(5)
