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

PAIR = "EURUSD-OTC"

AMOUNT = 20
EXPIRATION = 1  # 1 minuto

bot_active = True
last_candle_time = None
pending_signal = None

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
# CONEXIÓN IQ OPTION
# ==============================
print("🔌 Conectando...", flush=True)
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conexión", flush=True)
    exit()

print("✅ Conectado", flush=True)
send_telegram("🤖 BOT SNIPER ACTIVADO")

# ==============================
# ESPERAR SEGUNDO 59 (SNIPER)
# ==============================
def esperar_cierre_vela():
    while True:
        segundos = int(time.time()) % 60
        if segundos >= 59:
            break
        time.sleep(0.3)

# ==============================
# LOOP PRINCIPAL
# ==============================
while True:
    try:
        print("🟢 BOT ACTIVO...", flush=True)

        candles = Iq.get_candles(PAIR, 60, 100, time.time())

        if not candles:
            continue

        df = pd.DataFrame([{
            "open": c["open"],
            "close": c["close"],
            "max": c["max"],
            "min": c["min"]
        } for c in candles])

        current_time = candles[-1]["from"]

        # ==============================
        # NUEVA VELA DETECTADA
        # ==============================
        if last_candle_time != current_time:
            print("🟢 Nueva vela detectada", flush=True)

            # ==============================
            # EJECUTAR ENTRADA PENDIENTE
            # ==============================
            if pending_signal is not None:
                direccion, patron, score = pending_signal

                print(f"🚀 ENTRADA SNIPER: {direccion}", flush=True)

                send_telegram(
                    f"🎯 ENTRADA SNIPER\n"
                    f"{PAIR}\n"
                    f"Dirección: {direccion.upper()}\n"
                    f"Patrón: {patron}\n"
                    f"Score: {score}"
                )

                status, trade_id = Iq.buy(AMOUNT, PAIR, direccion, EXPIRATION)

                if status:
                    print("✅ OPERACIÓN ABIERTA", flush=True)

                    time.sleep(EXPIRATION * 60)

                    result = Iq.check_win_v4(trade_id)

                    # FIX tuple
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

                pending_signal = None

            # ==============================
            # ANALIZAR VELA CERRADA
            # ==============================
            print("🧠 Analizando cierre...", flush=True)

            signal = pro_signal(df)

            if signal is not None:
                direccion, patron, score = signal

                if direccion is not None:
                    print(f"🔥 Señal detectada: {direccion}", flush=True)

                    send_telegram(
                        f"📊 SEÑAL DETECTADA\n"
                        f"{PAIR}\n"
                        f"Dirección: {direccion.upper()}\n"
                        f"Patrón: {patron}\n"
                        f"Score: {score}\n"
                        f"⏳ Esperando apertura siguiente vela..."
                    )

                    # Guardar señal para siguiente vela
                    pending_signal = signal

            last_candle_time = current_time

        time.sleep(0.5)

    except Exception as e:
        print("❌ ERROR GENERAL:", e, flush=True)
        time.sleep(2)
