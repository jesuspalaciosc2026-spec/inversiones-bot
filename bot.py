import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from strategy import add_indicators, pro_signal

# -------------------------- CONFIGURACIÓN GENERAL --------------------------
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

# Credenciales desde variables de entorno
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

AMOUNT = float(os.getenv("TRADE_AMOUNT", 9))

# Lista dinámica de activos OTC (se carga al iniciar)
PAIRS = []

# Estados del bot
trade_open = False
last_trade_time = 0
bot_active = True
last_update_id = None
current_expiration = 1

# Marcos de tiempo
TF_M1 = 60    # 1 minuto
TF_M5 = 300   # 5 minutos
TF_HTF = 3600 # 1 HORA
# -------------------------------------------------------------------

# ================= CARGAR TODOS LOS ACTIVOS OTC DISPONIBLES =================
def cargar_activos_otc(iq):
    """Obtiene la lista completa de pares OTC que la API soporta"""
    global PAIRS
    try:
        # Obtener todos los activos activos
        todos_activos = iq.get_all_ACTIVES_OPTION()
        # Filtrar solo los que son OTC
        PAIRS = [activo for activo in todos_activos if activo.endswith("-OTC")]
        
        # Respaldo: si no se detectan, usar lista oficial completa
        if not PAIRS:
            PAIRS = [
                "AUDUSD-OTC", "CADCHF-OTC", "CADJPY-OTC", "CHFJPY-OTC", "CHFNOK-OTC",
                "EURCAD-OTC", "EURCHF-OTC", "EURGBP-OTC", "EURJPY-OTC", "EURTHB-OTC",
                "EURUSD-OTC", "GBPAUD-OTC", "GBPCAD-OTC", "GBPCHF-OTC", "GBPJPY-OTC",
                "GBPNZD-OTC", "GBPUSD-OTC", "NZDCAD-OTC", "NZDCHF-OTC", "NZDJPY-OTC",
                "NZDUSD-OTC", "USDCAD-OTC", "USDCHF-OTC", "USDJPY-OTC", "USDNOK-OTC",
                "USDSEK-OTC", "USDSGD-OTC"
            ]
        
        print(f"\n✅ ACTIVOS OTC CARGADOS: {len(PAIRS)} pares")
        print("📋 Lista: " + " | ".join(PAIRS[:12]) + ("..." if len(PAIRS) > 12 else ""))
        return PAIRS
    
    except Exception as e:
        print(f"⚠️ Error al detectar activos: {str(e)} | Usando lista base")
        PAIRS = ["EURUSD-OTC"]
        return PAIRS

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
        print(f"⚠️ Error Telegram: {str(e)}")

# ================= COMANDOS TELEGRAM =================
def check_telegram_commands():
    global bot_active, last_update_id
    if not TOKEN:
        return
    try:
        params = {"timeout":1, "offset": last_update_id} if last_update_id else {"timeout":1}
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params=params,
            timeout=5
        ).json()

        for res in r.get("result", []):
            last_update_id = res["update_id"] + 1
            txt = res.get("message", {}).get("text", "").strip().lower()
            if txt == "/stop":
                bot_active = False
                send_telegram("⛔ **BOT DETENIDO**")
            elif txt == "/start":
                bot_active = True
                send_telegram("✅ **BOT ACTIVADO**")
    except Exception:
        pass

# ================= CONEXIÓN IQ OPTION =================
def conectar_iq():
    iq = IQ_Option(EMAIL, PASSWORD)
    intentos = 0
    while intentos < 5:
        check, razon = iq.connect()
        if check:
            iq.change_balance("PRACTICE") # Cambia a "LIVE" para real
            print("✅ Conectado a IQ Option")
            send_telegram("🔥 **BOT INICIADO** | Analizando TODOS los pares OTC | Señales invertidas")
            return iq
        print(f"⚠️ Intento {intentos+1}: {razon}")
        intentos +=1
        time.sleep(10)
    print("❌ No se pudo conectar")
    send_telegram("❌ ERROR: No hay conexión a IQ Option")
    sys.exit(1)

# ================= OBTENER DATOS Y VELAS =================
def get_data(iq, par, tf):
    try:
        velas = iq.get_candles(par, tf, 40, time.time())
        # Respaldo: si falla con -OTC, intenta sin sufijo
        if not velas and par.endswith("-OTC"):
            par_simple = par.replace("-OTC", "")
            velas = iq.get_candles(par_simple, tf, 40, time.time())
        if not velas:
            return None
        df = pd.DataFrame(velas)
        df.rename(columns={"max":"high", "min":"low"}, inplace=True)
        return add_indicators(df)
    except Exception:
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
Expiración: {expiracion}min
ID: `{id_op}`"""
            print(msg)
            send_telegram(msg)
            return True
        return False
    except Exception as e:
        print(f"❌ Error operación: {str(e)}")
        return False

# ================= BUCLE PRINCIPAL =================
if __name__ == "__main__":
    if not EMAIL or not PASSWORD:
        print("❌ Define IQ_EMAIL y IQ_PASSWORD en variables de entorno")
        sys.exit(1)

    iq = conectar_iq()
    # Cargar automáticamente todos los pares OTC
    cargar_activos_otc(iq)
    print("\n🔍 Analizando pares OTC...")

    while True:
        try:
            check_telegram_commands()
            if not bot_active:
                time.sleep(2)
                continue

            # Esperar fin de vela para datos completos
            ts_servidor = int(iq.get_server_timestamp())
            if ts_servidor % 60 < 55:
                time.sleep(0.3)
                continue

            # Liberar operación finalizada
            if trade_open:
                if time.time() - last_trade_time > (current_expiration * 60) + 10:
                    trade_open = False
                    print("✅ Operación cerrada, listo para nueva señal")
                time.sleep(1)
                continue

            # Analizar cada par OTC
            for par in PAIRS:
                df_m1 = get_data(iq, par, TF_M1)
                df_m5 = get_data(iq, par, TF_M5)
                df_htf = get_data(iq, par, TF_HTF)

                # Validación segura de datos
                if any(df is None or df.empty for df in [df_m1, df_m5, df_htf]):
                    continue

                # Obtener e invertir señal
                señal_original, exp = pro_signal(df_m1, df_m5, df_htf)
                if señal_original:
                    señal_final = "put" if señal_original == "call" else "call"
                    abrir_operacion(iq, par, señal_final, exp)
                    break # Una operación por ciclo

            time.sleep(2)

        except Exception as e:
            print(f"❌ Error bucle: {str(e)}")
            send_telegram(f"⚠️ ERROR: {str(e)}")
            time.sleep(5)
