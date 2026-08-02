import os
import time
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal, update_result

# ==============================
# CONFIGURACIÓN
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

AMOUNT = 900
EXPIRATION = 1
MAX_OPERATIONS = 90

bot_active = True
operations_count = 0
last_candle_time = {}
last_update_id = None

# ==============================
# TELEGRAM (CORREGIDO)
# ==============================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        })

        resp = r.json()

        if not resp.get("ok"):
            print(f"❌ Error Telegram real: {resp}")
        else:
            print("📩 Enviado a Telegram")

    except Exception as e:
        print(f"❌ Error Telegram: {e}")


# ==============================
# COMANDOS TELEGRAM
# ==============================
def check_telegram_commands():
    global bot_active, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        r = requests.get(url)
        resp = r.json()

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
# CONEXIÓN IQ OPTION
# ==============================
print("🔌 Conectando a IQ Option...")
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error de conexión")
    exit()

print("✅ Conectado a IQ Option")
send_telegram("🤖 BOT INICIADO CORRECTAMENTE")

# ==============================
# LOOP PRINCIPAL
# ==============================
while True:
    try:
        check_telegram_commands()

        if not bot_active:
            time.sleep(2)
            continue

        if operations_count >= MAX_OPERATIONS:
            print("⛔ Límite alcanzado")
            send_telegram("🏁 Se alcanzó el límite de operaciones")
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

                # SOLO nueva vela
                if pair in last_candle_time and last_candle_time[pair] == current_time:
                    continue

                last_candle_time[pair] = current_time

                print(f"📊 Nueva vela → {pair}")

                direccion, patron, score = pro_signal(df, aggressive=True)

                if direccion is None:
                    continue

                # 🔥 INVERTIR SEÑAL
                direccion = "put" if direccion == "call" else "call"

                print(f"🔥 SEÑAL {pair}: {direccion.upper()} | score {score}")

                send_telegram(
                    f"📊 {pair}\n"
                    f"Señal: {direccion.upper()}\n"
                    f"Score: {score}"
                )

                # ==============================
                # ABRIR OPERACIÓN
                # ==============================
                status, trade_id = Iq.buy(AMOUNT, pair, direccion, EXPIRATION)

                if status:
                    operations_count += 1

                    print("✅ Operación abierta")
                    send_telegram(f"🚀 OPERACIÓN ABIERTA\n{pair} → {direccion.upper()}")

                    time.sleep(EXPIRATION * 60)

                    result = Iq.check_win_v4(trade_id)

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
