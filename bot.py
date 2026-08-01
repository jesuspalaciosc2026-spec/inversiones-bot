import time
import os
import sys
import requests
import pandas as pd
import datetime
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal

# =============================
# 🔥 FORZAR LOGS EN RAILWAY
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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD-OTC", "GBPUSD-OTC", "USDCHF-OTC", "EURJPY-OTC", "EURGBP-OTC"]

AMOUNT = 20
EXPIRATION = 1  # minutos

# =============================
# TELEGRAM
# =============================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        }, timeout=5)
    except:
        pass

# =============================
# CONEXIÓN IQ
# =============================
Iq = IQ_Option(EMAIL, PASSWORD)

def connect():
    global Iq

    log("🔌 Conectando a IQ Option...")
    Iq.connect()

    if Iq.check_connect():
        log("✅ Conectado a IQ Option")
        send_telegram("🤖 Bot conectado a IQ Option")
        return True
    else:
        log("❌ Error de conexión")
        return False

connect()

# =============================
# DATA
# =============================
def get_candles(pair, timeframe, count=60):
    try:
        data = Iq.get_candles(pair, timeframe, count, time.time())
        df = pd.DataFrame(data)

        # NORMALIZAR columnas
        if "max" in df.columns:
            df["high"] = df["max"]
        if "min" in df.columns:
            df["low"] = df["min"]

        return df

    except Exception as e:
        log(f"❌ Error obteniendo velas: {e}")
        return None

# =============================
# CONTROL DE VELA
# =============================
last_candle_time = {}

def is_new_candle(df, pair):
    global last_candle_time

    try:
        current_time = df.iloc[-1]["from"]

        if pair not in last_candle_time:
            last_candle_time[pair] = current_time
            return False

        if current_time != last_candle_time[pair]:
            last_candle_time[pair] = current_time
            log(f"🕯 Nueva vela detectada en {pair}")
            return True

        return False

    except:
        return False

# =============================
# TRADE
# =============================
def execute_trade(pair, direction):

    try:
        log(f"🚀 Ejecutando {direction.upper()} en {pair}")

        check, trade_id = Iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if check:
            log("✅ Operación abierta")
            send_telegram(f"✅ {pair} {direction.upper()}")

            time.sleep(EXPIRATION * 60)

            result = Iq.check_win_v4(trade_id)

            if result > 0:
                log(f"💰 WIN +{result}")
                send_telegram(f"💰 WIN {pair} +{result}")
            else:
                log(f"❌ LOSS {result}")
                send_telegram(f"❌ LOSS {pair} {result}")

        else:
            log("❌ No se pudo abrir operación")

    except Exception as e:
        log(f"❌ Error en trade: {e}")

# =============================
# LOOP PRINCIPAL
# =============================
log("🔥 BOT INICIADO")

while True:
    try:
        log("🔄 Bot activo...")

        # reconectar si se cae
        if not Iq.check_connect():
            log("⚠️ Reconectando...")
            connect()
            time.sleep(5)
            continue

        for pair in PAIRS:

            log(f"⏳ Analizando {pair}")

            df_m1 = get_candles(pair, 60, 60)
            df_m5 = get_candles(pair, 300, 60)

            if df_m1 is None or df_m5 is None:
                continue

            # SOLO UNA VEZ POR VELA
            if not is_new_candle(df_m1, pair):
                continue

            # =============================
            # SEÑAL
            # =============================
            direction, score, pattern = pro_signal(df_m1, df_m5)

            if direction is None:
                log("🚫 Sin señal")
                continue

            log(f"📊 Señal → {direction.upper()} | Score: {score} | {pattern}")

            # filtro mínimo
            if score < 20:
                log("⚠️ Score bajo, ignorado")
                continue

            send_telegram(f"📊 {pair}\n{direction.upper()} | Score {score}")

            # =============================
            # EJECUCIÓN
            # =============================
            execute_trade(pair, direction)

        time.sleep(1)

    except Exception as e:
        log(f"❌ ERROR GENERAL: {e}")
        time.sleep(5)
