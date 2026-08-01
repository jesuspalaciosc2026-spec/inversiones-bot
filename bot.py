import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal

# =============================
# CONFIG
# =============================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD", "GBPUSD", "EURJPY", "EURGBP"]

AMOUNT = 200
EXPIRATION = 1  # 1 minuto

# =============================
# TELEGRAM
# =============================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        })
    except:
        pass

# =============================
# CONEXIÓN
# =============================
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conectando")
    exit()

print("✅ Conectado a IQ Option")
send_telegram("🤖 Bot conectado")

# =============================
# FUNCIONES
# =============================
def get_candles(pair, timeframe, count):
    candles = Iq.get_candles(pair, timeframe, count, time.time())
    df = pd.DataFrame(candles)

    # NORMALIZAR columnas
    if "max" in df.columns:
        df["high"] = df["max"]
    if "min" in df.columns:
        df["low"] = df["min"]

    return df

# =============================
# CONTROL DE VELA
# =============================
last_candle_time = {}

def is_new_candle(df, pair):
    global last_candle_time

    current_time = df.iloc[-1]["from"]

    if pair not in last_candle_time:
        last_candle_time[pair] = current_time
        return False

    if current_time != last_candle_time[pair]:
        last_candle_time[pair] = current_time
        return True

    return False

# =============================
# LOOP PRINCIPAL
# =============================
while True:
    try:
        for pair in PAIRS:

            df_m1 = get_candles(pair, 60, 50)
            df_m5 = get_candles(pair, 300, 50)

            # Solo operar en vela nueva
            if not is_new_candle(df_m1, pair):
                continue

            # Obtener señal
            result = pro_signal(df_m1, df_m5)

            if result is None:
                continue

            direction, score, pattern = result

            print(f"🔥 {pair} | {direction} | score={score} | {pattern}")

            if score < 15:
                continue

            send_telegram(f"📊 {pair}\n📈 {direction.upper()}\n🔥 Score: {score}\n🎯 {pattern}")

            # Ejecutar operación
            check, id = Iq.buy(AMOUNT, pair, direction, EXPIRATION)

            if check:
                print("✅ Operación abierta")
                send_telegram(f"✅ Operación abierta {pair} {direction.upper()}")
            else:
                print("❌ Error al abrir operación")
                send_telegram(f"❌ Error al abrir operación {pair}")

        time.sleep(1)

    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        send_telegram(f"❌ ERROR: {e}")
        time.sleep(5)
