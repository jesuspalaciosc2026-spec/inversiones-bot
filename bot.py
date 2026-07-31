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

AMOUNT = 5500
PAIR = "EURUSD-OTC"

trade_open = False
last_trade_time = 0
bot_active = True
last_update_id = None
current_expiration = 1

# 🔥 CONTROL TIEMPO (CADA 2 MIN)
last_execution_time = 0
EXECUTION_INTERVAL = 120  # segundos (2 minutos)

# 🔥 CONTROL DE OPERACIONES
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

print("🔥 BOT ACTIVO (CADA 2 MIN - EURUSD-OTC)")
send("🔥 BOT ACTIVO (CADA 2 MIN - EURUSD-OTC)")

# ================= DATOS =================

def get_candles(pair, tf):
    try:
        data = iq.get_candles(pair, tf, 50, time.time())
        df = pd.DataFrame(data)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except Exception:
        return None

# ================= TRADE =================

def trade(pair, direction, expiration):
    global trade_open, last_trade_time, current_expiration, trade_count

    for _ in range(2):  # reintento

        status, result = iq.buy(AMOUNT, pair, direction, expiration)

        if status:
            trade_open = True
            last_trade_time = time.time()
            current_expiration = expiration
            trade_count += 1

            msg = f"🎯 {pair} {direction.upper()} ({expiration}m) | #{trade_count}"
            print(msg)
            send(msg)
            return

        time.sleep(1)

    print(f"❌ Falló operación en {pair}")

# ================= LOOP =================

while True:
    try:
        check_commands()

        if not bot_active:
            time.sleep(1)
            continue

        # 🔥 STOP 15 TRADES
        if trade_count >= MAX_TRADES:
            send("🛑 15 OPERACIONES COMPLETADAS")
            print("STOP 15 TRADES")
            break

        # ⏳ esperar cierre operación
        if trade_open:
            if time.time() - last_trade_time > current_expiration * 60:
                trade_open = False
            else:
                time.sleep(1)
                continue

        # ⏱️ CONTROL CADA 2 MINUTOS
        now = time.time()

        if now - last_execution_time < EXECUTION_INTERVAL:
            time.sleep(1)
            continue

        print("⏱️ EJECUTANDO ANÁLISIS...")

        df_m1 = get_candles(PAIR, 60)

        if df_m1 is None or len(df_m1) < 20:
            print("❌ Sin datos...")
            time.sleep(2)
            continue

        # 🧠 estrategia
        signal, expiration = pro_signal(df_m1)

        # 🔥 SIEMPRE OPERAR (fallback)
        direction = signal if signal else "call"

        trade(PAIR, direction, 1)

        last_execution_time = now

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
