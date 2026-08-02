import time
import os
import sys
import requests
import pandas as pd
import datetime
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal

# =============================
# LOGS EN RAILWAY
# =============================
sys.stdout.reconfigure(line_buffering=True)

def log(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

# =============================
# CONFIG
# =============================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🔥 SOLO OTC
PAIRS = ["EURUSD-OTC", "GBPUSD-OTC", "USDCHF-OTC"]

AMOUNT = 300
EXPIRATION = 1

# 🔥 LIMITE
max_trades = 90
trade_count = 0

# 🔥 INVERTIR SEÑALES
INVERT_SIGNALS = True

# =============================
# TELEGRAM
# =============================
def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# =============================
# CONTROL BOT
# =============================
bot_active = True
last_update_id = None

def check_commands():
    global bot_active, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"offset": last_update_id + 1} if last_update_id else {}

        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        for update in data.get("result", []):
            last_update_id = update["update_id"]

            msg = update.get("message", {}).get("text", "")

            if "/stop" in msg.lower():
                bot_active = False
                log("🛑 BOT DETENIDO")
                send("🛑 BOT DETENIDO")

            elif "/start" in msg.lower():
                bot_active = True
                log("🚀 BOT ACTIVADO")
                send("🚀 BOT ACTIVADO")

    except Exception as e:
        log(f"Error Telegram: {e}")

# =============================
# IQ OPTION
# =============================
Iq = IQ_Option(EMAIL, PASSWORD)

def connect():
    log("🔌 Conectando...")
    Iq.connect()

    if Iq.check_connect():
        log("✅ Conectado")
        send("🤖 Bot conectado")
    else:
        log("❌ Error conexión")

connect()

# =============================
# DATA
# =============================
def get_candles(pair, tf, count=60):
    try:
        data = Iq.get_candles(pair, tf, count, time.time())
        df = pd.DataFrame(data)

        if "max" in df.columns:
            df["high"] = df["max"]
        if "min" in df.columns:
            df["low"] = df["min"]

        return df
    except:
        return None

# =============================
# CONTROL VELA
# =============================
last_candle_time = {}

def is_new_candle(df, pair):
    global last_candle_time

    t = df.iloc[-1]["from"]

    if pair not in last_candle_time:
        last_candle_time[pair] = t
        return False

    if t != last_candle_time[pair]:
        last_candle_time[pair] = t
        log(f"🕯 Nueva vela {pair}")
        return True

    return False

# =============================
# TRADE
# =============================
def trade(pair, direction):
    global trade_count, bot_active

    try:
        if trade_count >= max_trades:
            bot_active = False
            log("🛑 LIMITE DE OPERACIONES ALCANZADO")
            send("🛑 Se alcanzaron 90 operaciones")
            return

        log(f"🚀 {pair} {direction.upper()}")

        status, trade_id = Iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            trade_count += 1

            send(f"🎯 {pair} {direction.upper()} ({trade_count}/9)")

            time.sleep(EXPIRATION * 60)

            result = Iq.check_win_v4(trade_id)

            if result > 0:
                log(f"💰 WIN {result}")
                send(f"💰 WIN {pair}")
            else:
                log(f"❌ LOSS {result}")
                send(f"❌ LOSS {pair}")

        else:
            log("❌ Error al abrir trade")

    except Exception as e:
        log(f"❌ Error trade: {e}")

# =============================
# LOOP PRINCIPAL
# =============================
log("🔥 BOT INICIADO")

while True:
    try:
        check_commands()

        if not Iq.check_connect():
            log("⚠️ Reconectando...")
            connect()
            time.sleep(5)
            continue

        if not bot_active:
            log("⏸ Bot en pausa...")
            time.sleep(2)
            continue

        for pair in PAIRS:

            df_m1 = get_candles(pair, 60)
            df_m5 = get_candles(pair, 300)

            if df_m1 is None or df_m5 is None:
                continue

            if not is_new_candle(df_m1, pair):
                continue

            direction, score, pattern = pro_signal(df_m1, df_m5)

            if direction is None:
                log(f"{pair} 🚫 sin señal")
                continue

            # 🔥 INVERTIR SEÑALES
            if INVERT_SIGNALS:
                if direction == "call":
                    direction = "put"
                elif direction == "put":
                    direction = "call"

            log(f"{pair} 📊 {direction} | score {score}")

            if score < 20:
                continue

            trade(pair, direction)

        time.sleep(1)

    except Exception as e:
        log(f"❌ ERROR GENERAL: {e}")
        time.sleep(5)
