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

AMOUNT = 20000
EXPIRATION = 1
MAX_OPERATIONS = 300

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
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print(f"❌ Error Telegram: {e}", flush=True)


# ==============================
# COMANDOS TELEGRAM
# ==============================
def check_telegram_commands():
    global bot_active, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        r = requests.get(url).json()

        for update in r.get("result", []):
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
        print("❌ Error comandos Telegram:", e, flush=True)


# ==============================
# CONEXIÓN IQ OPTION
# ==============================
print("🔌 Conectando a IQ Option...", flush=True)
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error de conexión", flush=True)
    exit()

print("✅ Conectado", flush=True)
send_telegram("🤖 BOT INICIADO")


# ==============================
# LOOP PRINCIPAL
# ==============================
while True:
    try:
        print("🟢 BOT ACTIVO...", flush=True)

        check_telegram_commands()

        if not bot_active:
            time.sleep(2)
            continue

        if operations_count >= MAX_OPERATIONS:
            print("⛔ Límite alcanzado...", flush=True)
            time.sleep(5)
            continue

        for pair in PAIRS:
            try:
                print(f"\n📊 Analizando {pair}", flush=True)

                candles = Iq.get_candles(pair, 60, 100, time.time())

                if not candles:
                    print("⚠️ Sin datos", flush=True)
                    continue

                df = pd.DataFrame([{
                    "open": c["open"],
                    "close": c["close"],
                    "max": c["max"],
                    "min": c["min"]
                } for c in candles])

                # 🔥 USAR VELA CERRADA
                current_time = candles[-2]["from"]

                if pair in last_candle_time and last_candle_time[pair] == current_time:
                    continue

                last_candle_time[pair] = current_time

                print("🧠 Buscando señal...", flush=True)

                signal = pro_signal(df)

                if signal is None:
                    print("❌ Sin señal", flush=True)
                    continue

                # 🔥 FIX ERROR TUPLA
                direccion, patron, score = signal

                print(f"🔥 SEÑAL {pair}: {direccion.upper()}", flush=True)

                send_telegram(
                    f"📊 {pair}\n"
                    f"Señal: {direccion.upper()}\n"
                    f"Score: {score}\n"
                    f"📌 Patrón: {patron}"
                )

                # ==============================
                # EJECUCIÓN
                # ==============================
                print("🚀 Ejecutando operación...", flush=True)

                status, trade_id = Iq.buy(AMOUNT, pair, direccion, EXPIRATION)

                if status:
                    operations_count += 1

                    print("✅ OPERACIÓN ABIERTA", flush=True)

                    send_telegram(
                        f"🚀 OPERACIÓN ABIERTA\n"
                        f"{pair} → {direccion.upper()}"
                    )

                    time.sleep(EXPIRATION * 60)

                    result = Iq.check_win_v4(trade_id)

                    # 🔥 FIX RESULT
                    if isinstance(result, tuple):
                        result = result[0]

                    try:
                        result = float(result)
                    except:
                        result = 0

                    update_result(result)

                    print(f"📈 Resultado: {result}", flush=True)
                    send_telegram(f"📈 Resultado: {result}")

                else:
                    print("❌ No se pudo abrir operación", flush=True)

            except Exception as e:
                print(f"❌ Error en {pair}: {e}", flush=True)

        time.sleep(1)

    except Exception as e:
        print("❌ ERROR GENERAL:", e, flush=True)
        time.sleep(5)
