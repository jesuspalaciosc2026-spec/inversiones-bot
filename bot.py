import os
import time
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal, update_result

# ==============================
# CONFIG
# ==============================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD-OTC", "GBPUSD-OTC", "USDCHF-OTC", "EURJPY-OTC"]

AMOUNT = 3333
EXPIRATION = 1
MAX_OPERATIONS = 15

bot_active = True
operations_count = 0
last_candle_time = {}
last_update_id = None

# ==============================
# TELEGRAM
# ==============================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except:
        pass

# ==============================
# COMANDOS
# ==============================
def check_telegram_commands():
    global bot_active, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        resp = requests.get(url).json()

        if not resp.get("ok"):
            return

        for update in resp.get("result", []):
            uid = update["update_id"]

            if last_update_id is None or uid > last_update_id:
                last_update_id = uid

                if "message" in update:
                    text = update["message"].get("text", "")

                    if text == "/stop":
                        bot_active = False
                        send_telegram("⛔ BOT DETENIDO")

                    elif text == "/start":
                        bot_active = True
                        send_telegram("✅ BOT ACTIVADO")
    except:
        pass

# ==============================
# 🧠 CONFIRMACIÓN FINAL (CLAVE 🔥)
# ==============================
def confirmacion_final(df, direccion):
    last = df.iloc[-1]

    if direccion == "call":
        return last["close"] >= last["open"]

    if direccion == "put":
        return last["close"] <= last["open"]

    return False

# ==============================
# 🎯 ESPERA + VALIDACIÓN SNIPER
# ==============================
def esperar_y_confirmar(df, direccion):
    while True:
        segundos = time.time() % 60

        # últimos 3 segundos
        if segundos >= 57:

            if confirmacion_final(df, direccion):
                print("✅ Confirmación final OK")
                return True
            else:
                print("❌ Cancelada por cambio de vela")
                return False

        time.sleep(0.1)

# ==============================
# CONEXIÓN
# ==============================
print("🔌 Conectando...")
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conexión")
    exit()

print("✅ Conectado")
send_telegram("🤖 SNIPER PRO MAX ACTIVADO")

# ==============================
# LOOP
# ==============================
while True:
    try:
        check_telegram_commands()

        if not bot_active:
            time.sleep(2)
            continue

        if operations_count >= MAX_OPERATIONS:
            send_telegram("🏁 Límite alcanzado")
            while True:
                time.sleep(60)

        for pair in PAIRS:
            try:
                candles = Iq.get_candles(pair, 60, 100, time.time())

                if not candles:
                    continue

                df = pd.DataFrame([{
                    "open": c["open"],
                    "close": c["close"],
                    "max": c["max"],
                    "min": c["min"]
                } for c in candles])

                current_time = candles[-1]["from"]

                if pair in last_candle_time and last_candle_time[pair] == current_time:
                    continue

                last_candle_time[pair] = current_time

                print(f"📊 {pair} nueva vela")

                # ==============================
                # SEÑAL
                # ==============================
                signal = pro_signal(df, aggressive=True)

                if not signal:
                    continue

                direccion = signal["direction"]
                score = signal["score"]

                print(f"🔥 {pair} → {direccion} | score {score}")

                send_telegram(f"{pair} → {direccion.upper()} | score {score}")

                # ==============================
                # 🎯 SNIPER PRO
                # ==============================
                print("⏳ Esperando confirmación final...")

                if not esperar_y_confirmar(df, direccion):
                    continue

                print("🎯 DISPARO SNIPER")

                status, trade_id = Iq.buy(AMOUNT, pair, direccion, EXPIRATION)

                if status:
                    operations_count += 1

                    send_telegram(f"🚀 {pair} → {direccion.upper()}")

                    time.sleep(EXPIRATION * 60)

                    result = Iq.check_win_v4(trade_id)

                    update_result(result)

                    send_telegram(f"📈 Resultado: {result}")

            except Exception as e:
                print(f"❌ Error en {pair}: {e}")

        time.sleep(1)

    except Exception as e:
        print("❌ ERROR GENERAL:", e)
        time.sleep(5)
