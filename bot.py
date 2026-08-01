import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal, update_result

# =========================================================
# 🔐 VARIABLES DE ENTORNO
# =========================================================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIR = "EURUSD"
AMOUNT = 2
EXPIRATION = 1  # 1 minuto


# =========================================================
# 📩 TELEGRAM
# =========================================================

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        })
    except Exception as e:
        print("Error Telegram:", e)


# =========================================================
# 🔌 CONEXIÓN IQ OPTION
# =========================================================

Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conectando a IQ Option")
    exit()

print("✅ Conectado a IQ Option")
send_telegram("🤖 Bot iniciado correctamente")


# =========================================================
# 🔄 LOOP PRINCIPAL
# =========================================================

while True:
    try:
        # =============================
        # OBTENER DATOS
        # =============================
        candles_m1 = Iq.get_candles(PAIR, 60, 50, time.time())
        candles_5s = Iq.get_candles(PAIR, 5, 50, time.time())

        if candles_m1 is None or candles_5s is None:
            print("⚠️ Datos no disponibles")
            time.sleep(5)
            continue

        df_m1 = pd.DataFrame(candles_m1)
        df_5s = pd.DataFrame(candles_5s)

        # =============================
        # GENERAR SEÑAL
        # =============================
        signal, expiration, pattern = pro_signal(df_m1, df_5s, aggressive=True)

        if signal:
            msg = f"🔥 SEÑAL {PAIR} → {signal.upper()} | patrón: {pattern}"
            print(msg)
            send_telegram(msg)

            # =============================
            # EJECUTAR OPERACIÓN
            # =============================
            check, trade_id = Iq.buy(AMOUNT, PAIR, signal, EXPIRATION)

            if check:
                print("✅ Operación abierta")
                send_telegram("✅ Operación ejecutada")

                # Esperar resultado
                time.sleep(EXPIRATION * 60)

                result = Iq.check_win_v4(trade_id)

                if result is None:
                    print("⚠️ Resultado no disponible")
                    send_telegram("⚠️ Resultado no disponible")
                    continue

                # =============================
                # RESULTADO
                # =============================
                if result > 0:
                    print("💰 WIN")
                    send_telegram("💰 WIN")
                    update_result(1, pattern)

                else:
                    print("❌ LOSS")
                    send_telegram("❌ LOSS")
                    update_result(0, pattern)

            else:
                print("❌ Error al abrir operación")
                send_telegram("❌ Error al abrir operación")

        # =============================
        # ESPERA ENTRE CICLOS
        # =============================
        time.sleep(5)

    except Exception as e:
        print("❌ ERROR GENERAL:", e)
        send_telegram(f"❌ ERROR: {e}")
        time.sleep(10)
