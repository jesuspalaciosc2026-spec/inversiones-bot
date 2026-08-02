import os
import time
import requests
from datetime import datetime
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

AMOUNT = 800
EXPIRATION = 1  # 1 minuto

MAX_OPERATIONS = 90

bot_active = True
operations_count = 0
last_candle_time = {}

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
    except:
        print("❌ Error enviando a Telegram")


# ==============================
# COMANDOS TELEGRAM
# ==============================
last_update_id = None

def check_telegram_commands():
    global bot_active, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        res = requests.get(url).json()

        for update in res["result"]:
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
        print("Error Telegram:", e)


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
send_telegram("🤖 BOT INICIADO")

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
            send_telegram("🏁 Límite de operaciones alcanzado")
            print("⛔ Bot detenido por límite")
            while True:
                time.sleep(60)

        for pair in PAIRS:
            try:
                candles = Iq.get_candles(pair, 60, 100, time.time())

                if not candles:
                    continue

                df = []
                for c in candles:
                    df.append({
                        "open": c["open"],
                        "close": c["close"],
                        "max": c["max"],
                        "min": c["min"]
                    })

                import pandas as pd
                df = pd.DataFrame(df)

                current_time = candles[-1]["from"]

                # 🔥 Solo operar nueva vela
                if pair in last_candle_time and last_candle_time[pair] == current_time:
                    continue

                last_candle_time[pair] = current_time

                print(f"📊 {pair} nueva vela analizada")

                direccion, patron, score = pro_signal(df, aggressive=True)

                if direccion is None:
                    continue

                # 🔥 INVERTIR SEÑALES
                direccion = "put" if direccion == "call" else "call"

                print(f"🔥 SEÑAL {pair} → {direccion.upper()} | score: {score}")

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

                    send_telegram(
                        f"🚀 OPERACIÓN ABIERTA\n"
                        f"{pair} → {direccion.upper()}"
                    )

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
