import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal

# ================= IMPORT SEGURO TV =================

try:
    from tvdatafeed import TvDatafeed, Interval
except Exception as e:
    print("❌ Error cargando tvDatafeed:", e)
    TvDatafeed = None

# ================= CONFIG =================

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

AMOUNT = 1800

PAIRS = [
    "EURUSD",
    "EURJPY",
    "EURGBP"
]

# ================= ESTADO =================

trade_open = False
last_trade_time = 0
bot_active = True
last_update_id = None
current_expiration = 1
last_candle_time = None

# ================= TELEGRAM =================

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
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

    except:
        pass

# ================= TRADINGVIEW =================

tv = None

if TvDatafeed:
    try:
        tv = TvDatafeed()
        print("✅ TradingView conectado")
    except Exception as e:
        print("❌ Error iniciando TradingView:", e)


def get_tv_data(symbol, timeframe, n=100):

    if tv is None:
        return None

    try:
        if timeframe == "M1":
            interval = Interval.in_1_minute
        elif timeframe == "M5":
            interval = Interval.in_5_minute
        else:
            interval = Interval.in_15_minute

        df = tv.get_hist(
            symbol=symbol,
            exchange="FX_IDC",
            interval=interval,
            n_bars=n
        )

        if df is None or df.empty:
            return None

        return df

    except Exception as e:
        print(f"❌ Error TV {symbol}: {e}")
        return None

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conexión IQ Option")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT ACTIVO (DATOS REALES)")
send("🔥 BOT ACTIVO (DATOS REALES)")

# ================= TRADE =================

def trade(pair, direction, expiration):
    global trade_open, last_trade_time, current_expiration

    status, _ = iq.buy(AMOUNT, pair, direction, expiration)

    if status:
        trade_open = True
        last_trade_time = time.time()
        current_expiration = expiration

        msg = f"🎯 {pair} {direction.upper()} ({expiration}m)"
        print(msg)
        send(msg)
    else:
        print(f"❌ Error ejecutando trade en {pair}")

# ================= LOOP =================

while True:
    try:
        check_commands()

        if not bot_active:
            time.sleep(1)
            continue

        # ===== CONTROL TRADE ACTIVO =====
        if trade_open:
            if time.time() - last_trade_time > current_expiration * 60:
                trade_open = False
            else:
                time.sleep(1)
                continue

        # ===== CONTROL DE VELA =====
        current_time = int(time.time())
        candle_time = current_time - (current_time % 60)

        if candle_time == last_candle_time:
            time.sleep(0.5)
            continue

        if current_time % 60 < 58:
            time.sleep(0.5)
            continue

        last_candle_time = candle_time
        print("🕯 Nueva vela detectada")

        # ===== ANALISIS =====
        for pair in PAIRS:

            print(f"🔎 Analizando {pair}")

            df_m1 = get_tv_data(pair, "M1")
            df_m5 = get_tv_data(pair, "M5")
            df_htf = get_tv_data(pair, "M15")

            if df_m1 is None or df_m5 is None or df_htf is None:
                print(f"⚠️ Sin datos para {pair}")
                continue

            signal, expiration = pro_signal(df_m1, df_m5, df_htf)

            if signal:
                trade(pair, signal, expiration)
                break

        time.sleep(1)

    except Exception as e:
        print("❌ Error general:", e)
        time.sleep(2)
