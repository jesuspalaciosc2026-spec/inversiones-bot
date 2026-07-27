import time
import os
import requests
import pandas as pd
import logging
import sys

from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal_multi

# ================= CONFIG =================

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

BASE_AMOUNT = 10000  # COP

PAIRS = ["EURUSD", "EURGBP", "EURJPY"]

trade_open = False
last_trade_time = 0
current_expiration = 1

MAX_TRADES_PER_DAY = 5
trade_count = 0

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conexión IQ Option")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT ACTIVO (DATOS REALES IQ OPTION)")

# ================= DATOS =================

def get_candles(pair, timeframe):
    try:
        data = iq.get_candles(pair, timeframe, 100, time.time())

        df = pd.DataFrame(data)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)

        df["open"] = df["open"].astype(float)
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)

        return df

    except:
        return None

# ================= TRADE =================

def trade(pair, direction, expiration):
    global trade_open, last_trade_time, trade_count

    if trade_count >= MAX_TRADES_PER_DAY:
        print("🚫 Límite diario alcanzado")
        return

    status, _ = iq.buy(BASE_AMOUNT, pair, direction, expiration)

    if status:
        trade_open = True
        last_trade_time = time.time()
        trade_count += 1

        print(f"🎯 TRADE: {pair} {direction.upper()} ${BASE_AMOUNT}")
    else:
        print(f"❌ Error al abrir trade en {pair}")

# ================= LOOP =================

while True:
    try:

        # Evitar múltiples trades simultáneos
        if trade_open:
            if time.time() - last_trade_time > current_expiration * 60:
                trade_open = False
            else:
                time.sleep(1)
                continue

        # Ejecutar solo al cierre de vela
        t = int(iq.get_server_timestamp())

        if t % 60 < 58:
            time.sleep(0.2)
            continue

        data = {}

        for pair in PAIRS:

            print(f"🔍 Analizando {pair}")

            df_m1 = get_candles(pair, 60)
            df_m5 = get_candles(pair, 300)
            df_m15 = get_candles(pair, 900)

            if df_m1 is None or df_m5 is None or df_m15 is None:
                print(f"⚠️ Sin datos para {pair}")
                continue

            data[pair] = (df_m1, df_m5, df_m15)

        # Solo si tenemos todos los pares
        if len(data) < 3:
            continue

        # ================= SEÑAL =================
        pair, signal, expiration = pro_signal_multi(data)

        if signal:
            trade(pair, signal, expiration)

        time.sleep(1)

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(1)
