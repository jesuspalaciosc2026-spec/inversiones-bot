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

AMOUNT = 2000

PAIRS = [
    "EURUSD",
    "GBPUSD",
    "EURGBP",
    "USDCHF",
    "EURJPY"
]

trade_open = False
last_trade_time = 0
bot_active = True
last_update_id = None
current_expiration = 1
last_candle_time = {}

# 🔥 NUEVO
trade_count = 0
MAX_TRADES = 15

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


def check_commands():
    global bot_active, last_update_id

    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={"timeout": 1, "offset": last_update_id},
            timeout=5
        ).json()

        for result in r.get("result", []):
            last_update_id = result["update_id"] + 1
            text = result.get("message", {}).get("text", "")

            if text == "/stop":
                bot_active = False
                send("⛔ BOT DETENIDO")

            elif text == "/start":
                bot_active = True
                send("✅ BOT ACTIVADO")

    except Exception:
        pass

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error de conexión con IQ Option")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT ACTIVO")
send("🔥 BOT ACTIVO")

# ================= DATOS =================

def get_candles(pair, tf):
    try:
        data = iq.get_candles(pair, tf, 30, time.time())
        df = pd.DataFrame(data)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except Exception:
        return None

# ================= TRADE =================

def trade(pair, direction, expiration):
    global trade_open, last_trade_time, current_expiration, trade_count

    status, _ = iq.buy(AMOUNT, pair, direction, expiration)

    if status:
        trade_open = True
        last_trade_time = time.time()
        current_expiration = expiration
        trade_count += 1

        msg = f"🎯 {pair} {direction.upper()} ({expiration}m) | #{trade_count}"
        print(msg)
        send(msg)

# ================= LOOP =================

while True:
    try:
        check_commands()

        if not bot_active:
            time.sleep(1)
            continue

        # 🔥 DETENER DESPUÉS DE 15 TRADES
        if trade_count >= MAX_TRADES:
            send("🛑 15 OPERACIONES COMPLETADAS")
            print("STOP 15 TRADES")
            break

        if trade_open:
            if time.time() - last_trade_time > current_expiration * 60:
                trade_open = False
            else:
                time.sleep(1)
                continue

        # 🔥 NUEVA VELA
        t = int(iq.get_server_timestamp())
        if t % 60 > 5:
            time.sleep(0.2)
            continue

        for pair in PAIRS:

            df_m1 = get_candles(pair, 60)
            df_m5 = get_candles(pair, 300)
            df_1s = get_candles(pair, 1)

            if df_1s is None or len(df_1s) < 10:
                continue

            current_candle = df_m1["from"].iloc[-1]

            if last_candle_time.get(pair) == current_candle:
                continue

            signal, expiration = pro_signal(df_m1, df_m5, df_1s)

            if signal:
                trade(pair, signal, expiration)
                last_candle_time[pair] = current_candle
                break

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
