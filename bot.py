import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from strategy import add_indicators, pro_signal

# -------------------------- CONFIGURACIÓN --------------------------
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

# Lee credenciales desde variables de entorno (seguro para Railway/GitHub)
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

AMOUNT = float(os.getenv("TRADE_AMOUNT", 9))  # Monto por operación

# Activos OTC a analizar
PAIRS = [
    "AUDUSD-OTC", "CADCHF-OTC", "CADJPY-OTC", "CHFJPY-OTC", "CHFNOK-OTC",
    "EURCAD-OTC", "EURCHF-OTC", "EURGBP-OTC", "EURJPY-OTC", "EURTHB-OTC",
    "EURUSD-OTC", "GBPAUD-OTC", "GBPCAD-OTC", "GBPCHF-OTC", "GBPJPY-OTC",
    "GBPNZD-OTC", "GBPUSD-OTC"
]

# Estados del bot
trade_open = False
last_trade_time = 0
bot_active = True
last_update_id = None
current_expiration = 1

# Marcos de tiempo (coinciden con strategy.py)
TF_M1 = 60    # 1 minuto
TF_M5 = 300   # 5 minutos
TF_HTF = 3600 # 1 HORA (antes usabas 15min, actualizado para mejor precisión)
# -------------------------------------------------------------------

# ================= NOTIFICACIONES TELEGRAM =================
def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"⚠️ Error al enviar a Telegram: {str(e)}")

# ================= COMANDOS TELEGRAM =================
def check_telegram_commands():
    global bot_active, last_update_id
    if not TOKEN:
        return
    try:
        params = {"timeout": 1, "offset": last_update_id} if last_update_id else {"timeout": 1}
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params=params,
            timeout=5
        ).json()

        for result in r.get("result", []):
            last_update_id = result["update_id"] + 1
            text = result.get("message", {}).get("text", "").strip().lower()

            if text == "/stop":
                bot_active = False
                send_telegram("⛔ **BOT DETENIDO** por comando")
            elif text == "/start":
                bot_active = True
                send_telegram("✅ **BOT ACTIVADO** por comando")
    except Exception:
        pass

# ================= CONEXIÓN IQ OPTION =================
def conectar_iq():
    iq = IQ_Option(EMAIL, PASSWORD)
    intentos = 0
    while intentos < 5:
        check, razon = iq.connect()
        if check:
            iq.change_balance("PRACTICE")  # Cambia a "LIVE" para real
            print("✅ Conectado exitosamente a IQ Option")
            send_telegram("🔥 **BOT INICIADO** | MODO: SEÑALES INVERTIDAS | CUENTA: PRÁCTICA")
            return iq
        print(f"⚠️ Intento {intentos+1} fallido: {razon}")
        intentos += 1
        time.sleep(10)
    print("❌ No se pudo conectar a IQ Option")
    send_telegram("❌ ERROR: No se pudo conectar a IQ Option")
    sys.exit(1)

# ================= OBTENER VELAS E INDICADORES =================
def get_data(iq, par, tf):
    try:
        velas = iq.get_candles(par, tf, 40, time.time())
        if not velas:
            return None
        df = pd.DataFrame(velas)
        # Renombrar columnas al formato que usa la estrategia
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return add_indicators(df)
    except Exception as e:
        print(f"⚠️ Datos no disponibles para {par}: {str(e)}")
        return None

# ================= EJECUTAR OPERACIÓN =================
def abrir_operacion(iq, par, direccion, expiracion):
    global trade_open, last_trade_time, current_expiration
    try:
        ok, id_op = iq.buy(AMOUNT, par, direccion, expiracion)
        if ok:
            trade_open = True
            last_trade_time = time.time()
            current_expiration = expiracion
            msg = f"""🎯 **OPERACIÓN ABIERTA**
Activo: `{par}`
Dirección: `{direccion.upper()}` (INVERTIDA)
Monto: `${AMOUNT}`
Expiración: {expiracion} minutos
ID: `{id_op}`"""
            print(msg)
            send_telegram(msg)
            return True
        else:
            print(f"❌ Falló operación en {par}: {id_op}")
            send_telegram(f"❌ FALLÓ APERTURA | {par} | {direccion.upper()}")
            return False
    except Exception as e:
        print(f"❌ Error al operar: {str(e)}")
        send_telegram(f"❌ ERROR DE EJECUCIÓN: {str(e)}")
        return False

# ================= BUCLE PRINCIPAL =================
if __name__ == "__main__":
    if not EMAIL or not PASSWORD:
        print("❌ Define las variables de entorno IQ_EMAIL y IQ_PASSWORD")
        sys.exit(1)

    iq = conectar_iq()
    print("🔍 Iniciando análisis de activos OTC...")

    while True:
        try:
            check_telegram_commands()
            if not bot_active:
                time.sleep(2)
                continue

            # Esperar fin de vela para evitar señales incompletas
            servidor_tiempo = int(iq.get_server_timestamp())
            if servidor_tiempo % 60 < 55:
                time.sleep(0.3)
                continue

            # Liberar estado si ya venció la operación anterior
            if trade_open:
                if time.time() - last_trade_time > (current_expiration * 60) + 10:
                    trade_open = False
                    print("✅ Operación finalizada, listo para nueva señal")
                time.sleep(1)
                continue

            # Analizar cada activo
            for par in PAIRS:
                df_m1 = get_data(iq, par, TF_M1)
                df_m5 = get_data(iq, par, TF_M5)
                df_htf = get_data(iq, par, TF_HTF)

                if not all([df_m1, df_m5, df_htf]):
                    continue

                # Obtener señal e INVERTIRLA como pediste
                señal_original, expiracion = pro_signal(df_m1, df_m5, df_htf)
                if señal_original:
                    señal_final = "put" if señal_original.lower() == "call" else "call"
                    abrir_operacion(iq, par, señal_final, expiracion)
                    break  # Una operación por ciclo

            time.sleep(2)

        except Exception as e:
            print(f"❌ Error en bucle: {str(e)}")
            send_telegram(f"⚠️ ERROR EN BOT: {str(e)}")
            time.sleep(5)
