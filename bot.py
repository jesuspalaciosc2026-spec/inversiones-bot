import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

AMOUNT = 5580
PAIR = "EURUSD-OTC"

trade_open = False
last_trade_time = 0
current_expiration = 1

# ================= TELEGRAM =================

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except Exception:
        pass


# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conexión")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT ACTIVO")
send("🔥 BOT ACTIVO")


# ================= DATOS =================

def get_candles(pair, tf, count=50):
    try:
        data = iq.get_candles(pair, tf, count, time.time())
        df = pd.DataFrame(data)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None


# ================= TRADE =================

def trade(direction):

    global trade_open, last_trade_time

    status, _ = iq.buy(AMOUNT, PAIR, direction, 1)

    if status:
        trade_open = True
        last_trade_time = time.time()

        msg = f"🎯 {PAIR} {direction.upper()} (1m)"
        print(msg)
        send(msg)


# ================= LOOP =================

while True:
    try:

        # evitar múltiples operaciones
        if trade_open:
            if time.time() - last_trade_time > 60:
                trade_open = False
            else:
                time.sleep(0.5)
                continue

        t = int(iq.get_server_timestamp())

        # 🔥 SOLO SEGUNDO 58
        if t % 60 < 58:
            time.sleep(0.2)
            continue

        df_m1 = get_candles(PAIR, 60, 50)
        df_5s = get_candles(PAIR, 5, 50)

        if df_m1 is None or df_5s is None:
            continue

        signal, expiration = pro_signal(df_m1, df_5s)

        if signal:
            trade(signal)

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
