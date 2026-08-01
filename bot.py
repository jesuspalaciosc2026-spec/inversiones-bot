import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

from strategy import pro_signal, update_result


# =========================================================
# 🔐 CONFIG
# =========================================================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD", "GBPUSD", "USDCHF", "EURJPY", "EURGBP"]

AMOUNT = 2
EXPIRATION = 1  # 1 minuto


# =========================================================
# 📲 TELEGRAM
# =========================================================

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        }
        requests.post(url, data=data)
    except:
        print("Error enviando a Telegram")


# =========================================================
# 📊 DATA
# =========================================================

def get_candles(iq, pair, timeframe, count):
    try:
        candles = iq.get_candles(pair, timeframe, count, time.time())
        df = pd.DataFrame(candles)

        if df.empty:
            return None

        df = df.rename(columns={
            "max": "high",
            "min": "low"
        })

        return df

    except:
        return None


# =========================================================
# 🚀 CONEXIÓN
# =========================================================

print("🔌 Conectando a IQ Option...")
iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error al conectar")
    exit()

print("✅ Conectado a IQ Option")
send_telegram("🤖 Bot conectado correctamente")


# =========================================================
# 🔁 LOOP PRINCIPAL
# =========================================================

while True:
    try:

        for pair in PAIRS:

            df_m1 = get_candles(iq, pair, 60, 50)
            df_5s = get_candles(iq, pair, 5, 50)

            if df_m1 is None or df_5s is None:
                continue

            # 🔥 SIN aggressive aquí
            direction, exp, pattern = pro_signal(df_m1, df_5s)

            if direction is None:
                continue

            print(f"🔥 SEÑAL {pair} → {direction.upper()}")

            send_telegram(f"📊 {pair} → {direction.upper()}")

            # =================================================
            # 💰 EJECUTAR OPERACIÓN
            # =================================================

            check, trade_id = iq.buy(AMOUNT, pair, direction, EXPIRATION)

            if not check:
                print("❌ Error al abrir operación")
                continue

            print("⏳ Esperando resultado...")

            time.sleep(EXPIRATION * 60 + 2)

            result = iq.check_win_v4(trade_id)

            if result is None:
                print("⚠️ No se pudo obtener resultado")
                continue

            win = 1 if result > 0 else 0

            # 🧠 ACTUALIZAR IA
            update_result(win, pattern)

            if win:
                msg = f"✅ WIN {pair} ({direction})"
            else:
                msg = f"❌ LOSS {pair} ({direction})"

            print(msg)
            send_telegram(msg)

            time.sleep(2)

        time.sleep(1)

    except Exception as e:
        print("❌ ERROR GENERAL:", e)
        time.sleep(5)
