import time
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import generate_signal
import os
import requests

# ==============================
# CONFIG
# ==============================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD", "GBPUSD", "EURGBP", "USDCHF", "EURJPY"]

AMOUNT = 1000
TIMEFRAME = 60  # 1 minuto
EXPIRATION = 1  # 1 minuto

trade_open = False
last_trade_time = 0

# ==============================
# TELEGRAM
# ==============================

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
        response = requests.post(url, data=data).json()

        if not response.get("ok"):
            print("Error Telegram:", response)

    except Exception as e:
        print("Error enviando Telegram:", e)

# ==============================
# CONEXIÓN IQ OPTION
# ==============================

API = IQ_Option(EMAIL, PASSWORD)
API.connect()

if not API.check_connect():
    print("❌ Error conectando")
    exit()
else:
    print("✅ Conectado correctamente")

# ==============================
# FUNCIONES
# ==============================

def get_candles(pair, timeframe=60, count=50):
    candles = API.get_candles(pair, timeframe, count, time.time())
    df = pd.DataFrame(candles)

    df["open"] = df["open"]
    df["close"] = df["close"]
    df["high"] = df["max"]
    df["low"] = df["min"]

    return df


# ==============================
# LOOP PRINCIPAL
# ==============================

print("🚀 BOT INICIADO")

while True:
    try:
        for pair in PAIRS:

            df = get_candles(pair)

            signal = generate_signal(df)

            current_time = time.time()

            # Evitar sobreoperar (1 operación cada 60s)
            if trade_open and current_time - last_trade_time < 60:
                continue

            if signal and not trade_open:

                direction = signal["direction"]
                score = signal["score"]

                print(f"📊 Señal en {pair} | Dirección: {direction} | Score: {score}")

                if score >= 6:

                    status, trade_id = API.buy(AMOUNT, pair, direction, EXPIRATION)

                    if status:
                        trade_open = True
                        last_trade_time = current_time

                        msg = f"""
📈 NUEVA OPERACIÓN

Par: {pair}
Dirección: {direction.upper()}
Monto: {AMOUNT}
Score: {score}
Expiración: 1 minuto
"""
                        print(msg)
                        send_telegram(msg)

                        # Esperar resultado
                        time.sleep(60)

                        result = API.check_win_v4(trade_id)

                        if result > 0:
                            print(f"✅ GANANCIA: {result}")
                            send_telegram(f"✅ GANANCIA: {result}")
                        else:
                            print(f"❌ PÉRDIDA: {result}")
                            send_telegram(f"❌ PÉRDIDA: {result}")

                        trade_open = False

        time.sleep(2)

    except Exception as e:
        print("⚠️ Error:", e)
        time.sleep(5)
