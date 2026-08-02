import os
import time
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# 🔥 IMPORTANTE
from strategy import signal_5m, confirmacion_1m, update_result

# ==============================
# CONFIG
# ==============================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC"
]

AMOUNT = 13000
EXPIRATION = 1

bot_active = True
last_candle_time = {}
last_update_id = None

# ==============================
# TELEGRAM
# ==============================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("❌ Error Telegram:", e)

# ==============================
# COMANDOS TELEGRAM
# ==============================
def check_telegram_commands():
    global bot_active, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        resp = requests.get(url).json()

        if not resp.get("ok"):
            return

        for update in resp.get("result", []):
            update_id = update["update_id"]

            if last_update_id is None or update_id > last_update_id:
                last_update_id = update_id

                if "message" in update:
                    text = update["message"].get("text", "")

                    if text == "/stop":
                        bot_active = False
                        send_telegram("⛔ BOT DETENIDO")

                    elif text == "/start":
                        bot_active = True
                        send_telegram("✅ BOT ACTIVADO")

    except Exception as e:
        print("❌ Error comandos Telegram:", e)

# ==============================
# SNIPER TIMING
# ==============================
def esperar_cierre():
    while True:
        segundos = int(time.time() % 60)
        if segundos >= 58:
            return
        time.sleep(0.2)

# ==============================
# CONEXIÓN IQ OPTION
# ==============================
print("🔌 Conectando...")
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conexión")
    exit()

print("✅ Conectado")
send_telegram("🤖 BOT HÍBRIDO 5M + 1M ACTIVADO")

# ==============================
# LOOP PRINCIPAL
# ==============================
while True:
    try:
        check_telegram_commands()

        if not bot_active:
            time.sleep(2)
            continue

        for pair in PAIRS:
            try:
                # ======================
                # 📊 DATOS 5M
                # ======================
                candles_5m = Iq.get_candles(pair, 300, 100, time.time())

                if not candles_5m:
                    continue

                df_5m = pd.DataFrame([{
                    "open": c["open"],
                    "close": c["close"],
                    "max": c["max"],
                    "min": c["min"]
                } for c in candles_5m])

                current_time = candles_5m[-1]["from"]

                if pair in last_candle_time and last_candle_time[pair] == current_time:
                    continue

                last_candle_time[pair] = current_time

                print(f"📊 {pair} nueva vela 5M")

                # ======================
                # 🧠 SEÑAL 5M
                # ======================
                signal = signal_5m(df_5m)

                if not signal:
                    continue

                direccion = signal["direction"]
                motivos = signal["reason"]

                print(f"🔥 Señal 5M: {direccion}")

                # ======================
                # 📊 DATOS 1M
                # ======================
                candles_1m = Iq.get_candles(pair, 60, 50, time.time())

                df_1m = pd.DataFrame([{
                    "open": c["open"],
                    "close": c["close"],
                    "max": c["max"],
                    "min": c["min"]
                } for c in candles_1m])

                # ======================
                # 🎯 CONFIRMACIÓN 1M
                # ======================
                confirm = confirmacion_1m(df_1m)

                if confirm != direccion:
                    print("❌ No confirmó en 1M")
                    continue

                print("🎯 Confirmación 1M OK")

                # ======================
                # 📩 MENSAJE TELEGRAM
                # ======================
                msg = f"📊 {pair}\n"
                msg += f"Dirección: {direccion.upper()}\n\n"
                msg += "📌 Motivo:\n"

                for m in motivos:
                    msg += f"✔ {m}\n"

                msg += "\n✔ Confirmación en 1M"

                send_telegram(msg)

                # ======================
                # ⏳ ESPERA SNIPER
                # ======================
                esperar_cierre()

                # ======================
                # 🚀 EJECUTAR
                # ======================
                status, trade_id = Iq.buy(AMOUNT, pair, direccion, EXPIRATION)

                if status:
                    print("✅ OPERACIÓN ABIERTA")
                    send_telegram(f"🚀 {pair} → {direccion.upper()}")

                    time.sleep(EXPIRATION * 60)

                    result = Iq.check_win_v4(trade_id)

                    if isinstance(result, tuple):
                        result = result[0]

                    update_result(result)

                    send_telegram(f"📈 Resultado: {result}")

                else:
                    print("❌ Error al abrir operación")

            except Exception as e:
                print(f"❌ Error en {pair}: {e}")

        time.sleep(1)

    except Exception as e:
        print("❌ ERROR GENERAL:", e)
        time.sleep(5)
