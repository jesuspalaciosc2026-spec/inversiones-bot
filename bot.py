import time
import os
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal, update_ai

# =========================================================
# 🔐 CONFIG
# =========================================================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

AMOUNT = 200
EXPIRATION = 1  # 1 minuto

PAIRS = ["EURUSD", "GBPUSD", "EURJPY", "USDCHF", "EURGBP"]

# =========================================================
# 🚀 CONEXIÓN
# =========================================================

Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conectando a IQ Option")
    exit()

print("✅ Conectado a IQ Option")

# =========================================================
# 🔄 VARIABLES CONTROL
# =========================================================

trade_open = False
last_trade_time = 0
TRADE_COOLDOWN = 60  # segundos (evita spam)

# =========================================================
# 📊 OBTENER DATOS
# =========================================================

def get_candles(pair, timeframe, count):
    candles = Iq.get_candles(pair, timeframe, count, time.time())
    import pandas as pd
    df = pd.DataFrame(candles)
    df.rename(columns={
        "max": "high",
        "min": "low"
    }, inplace=True)
    return df

# =========================================================
# 🎯 LOOP PRINCIPAL
# =========================================================

while True:
    try:
        # evitar operar muy seguido
        if time.time() - last_trade_time < TRADE_COOLDOWN:
            time.sleep(1)
            continue

        # evitar múltiples operaciones abiertas
        if trade_open:
            time.sleep(1)
            continue

        for pair in PAIRS:

            # =============================
            # VALIDAR SI ESTÁ ABIERTO
            # =============================
            open_assets = Iq.get_all_open_time()

            if not open_assets["binary"][pair]["open"]:
                print(f"⛔ {pair} cerrado")
                continue

            # =============================
            # DATOS
            # =============================
            df_m1 = get_candles(pair, 60, 50)
            df_5s = get_candles(pair, 5, 50)

            # =============================
            # SEÑAL
            # =============================
            direction, exp, pattern = pro_signal(df_m1, df_5s)

            if direction is None:
                continue

            print(f"🔥 SEÑAL {pair} → {direction.upper()} | patrón: {pattern}")

            # =============================
            # EJECUCIÓN REAL
            # =============================
            status, trade_id = Iq.buy(AMOUNT, pair, direction, EXPIRATION)

            if status:
                print(f"✅ OPERACIÓN ABIERTA → {pair} {direction}")
                trade_open = True
                last_trade_time = time.time()

                # =============================
                # RESULTADO
                # =============================
                result = Iq.check_win_v4(trade_id)

                if result > 0:
                    print("💰 WIN")
                    update_ai(1, pattern)
                else:
                    print("❌ LOSS")
                    update_ai(0, pattern)

                trade_open = False

            else:
                print(f"❌ ERROR al abrir operación en {pair}")
                time.sleep(2)  # evita spam

        time.sleep(1)

    except Exception as e:
        print("⚠️ ERROR GENERAL:", e)
        time.sleep(5)
