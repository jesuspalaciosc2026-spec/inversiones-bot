import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal, update_result

# =============================
# CONFIG
# =============================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIR = "EURUSD"
AMOUNT = 200
EXPIRATION = 1

# =============================
# TELEGRAM
# =============================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except:
        pass

# =============================
# CONEXION
# =============================
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

print("✅ Conectado a IQ Option")

# =============================
# CONTROL DE VELA
# =============================
last_candle_time = 0
trade_open = False

# =============================
# LOOP PRINCIPAL
# =============================
while True:
    try:
        current_time = int(time.time() // 60)

        # 👉 SOLO EJECUTA EN NUEVA VELA
        if current_time != last_candle_time:
            last_candle_time = current_time
            trade_open = False

            # =============================
            # DATOS
            # =============================
            candles_m1 = Iq.get_candles(PAIR, 60, 50, time.time())
            candles_5s = Iq.get_candles(PAIR, 5, 50, time.time())

            import pandas as pd
            df_m1 = pd.DataFrame(candles_m1)
            df_5s = pd.DataFrame(candles_5s)

            # =============================
            # SEÑAL
            # =============================
            direction, expiration, pattern = pro_signal(
                df_m1, df_5s, aggressive=True
            )

            if direction is None:
                print("⏸️ Sin señal")
                continue

            print(f"🔥 SEÑAL {PAIR} → {direction.upper()}")

            send_telegram(f"🔥 {PAIR} → {direction.upper()}")

            # =============================
            # ENTRADA EN NUEVA VELA
            # =============================
            check, id = Iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

            if check:
                print("✅ Operación abierta")
                send_telegram("✅ Operación abierta")

                trade_open = True

                # =============================
                # RESULTADO
                # =============================
                time.sleep(EXPIRATION * 60)

                result = Iq.check_win_v4(id)

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

        time.sleep(1)

    except Exception as e:
        print("❌ ERROR:", e)
        time.sleep(5)
