import time
import os
import requests
import pandas as pd
import logging
import sys

from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal_multi

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

BASE_AMOUNT = 10000  # USD

PAIRS = ["EURUSD", "EURGBP", "EURJPY"]

trade_open = False
last_trade_time = 0
current_expiration = 1

MAX_TRADES_PER_DAY = 1
trade_count = 0

# ================= DATOS BINANCE =================

def get_data(symbol="BTCUSDT", interval="1m", limit=100):

    url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    try:
        data = requests.get(url, params=params, timeout=5).json()

        df = pd.DataFrame(data, columns=[
            "time","open","high","low","close","volume",
            "_","_","_","_","_","_"
        ])

        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)

        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df.set_index("time", inplace=True)

        return df

    except:
        return None


# ================= MAPEO =================

PAIR_MAP = {
    "EURUSD": "BTCUSDT",
    "EURGBP": "ETHUSDT",
    "EURJPY": "BTCUSDT"
}


# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conexión")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT ULTRA SELECTIVO ACTIVO")


# ================= TRADE =================

def trade(pair, direction, expiration):
    global trade_open, last_trade_time, trade_count

    if trade_count >= MAX_TRADES_PER_DAY:
        return

    status, _ = iq.buy(BASE_AMOUNT, pair, direction, expiration)

    if status:
        trade_open = True
        last_trade_time = time.time()
        trade_count += 1

        print(f"🎯 {pair} {direction.upper()} ${BASE_AMOUNT}")


# ================= LOOP =================

while True:
    try:

        if trade_open:
            if time.time() - last_trade_time > current_expiration * 60:
                trade_open = False
            else:
                time.sleep(1)
                continue

        t = int(time.time())

        # entrar en últimos segundos
        if t % 60 < 58:
            time.sleep(0.1)
            continue

        data = {}

        for pair in PAIRS:

            symbol = PAIR_MAP[pair]

            df_m1 = get_data(symbol, "1m")
            df_m5 = get_data(symbol, "5m")
            df_htf = get_data(symbol, "15m")

            if df_m1 is None or df_m5 is None or df_htf is None:
                continue

            data[pair] = (df_m1, df_m5, df_htf)

        if len(data) == 3:

            pair, signal, expiration = pro_signal_multi(data)

            if signal:
                trade(pair, signal, expiration)

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
