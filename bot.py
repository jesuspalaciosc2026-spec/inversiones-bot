import time
from datetime import datetime
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal

# =========================
# CONFIGURACIÓN
# =========================
EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

PAIR = "EURUSD-OTC"
AMOUNT = 75
EXPIRATION = 1  # 1 minuto

# =========================
# CONEXIÓN
# =========================
iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error de conexión")
    exit()
else:
    print("✅ Conectado")

iq.change_balance("PRACTICE")

# =========================
# VARIABLES CONTROL
# =========================
last_candle_time = None
operacion_ejecutada = False

# =========================
# LOOP PRINCIPAL
# =========================
while True:
    try:
        # Obtener velas (M1)
        candles = iq.get_candles(PAIR, 60, 50, time.time())

        if not candles:
            time.sleep(1)
            continue

        # Tiempo de la última vela
        current_candle_time = candles[-1]["from"]

        # =========================
        # DETECTAR NUEVA VELA
        # =========================
        if last_candle_time != current_candle_time:
            last_candle_time = current_candle_time
            operacion_ejecutada = False

            print("🟢 Nueva vela detectada")

            # Convertir a formato tipo DataFrame simple
            df = candles

            # =========================
            # ANALIZAR VELA CERRADA
            # =========================
            signal = pro_signal(df)

            if signal:
                print(f"🔥 SEÑAL DETECTADA: {signal.upper()}")

                # =========================
                # EJECUTAR EN APERTURA SIGUIENTE
                # =========================
                check, id = iq.buy(AMOUNT, PAIR, signal, EXPIRATION)

                if check:
                    print(f"✅ OPERACIÓN EJECUTADA → {signal.upper()}")
                    operacion_ejecutada = True
                else:
                    print("❌ Error al ejecutar operación")

        # =========================
        # EVITAR SPAM
        # =========================
        time.sleep(1)

    except Exception as e:
        print("❌ ERROR:", e)
        time.sleep(2)
