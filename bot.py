# bot.py
import os
import time
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import pro_signal, update_result

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD-OTC","GBPUSD-OTC","USDCHF-OTC","EURJPY-OTC"]
AMOUNT = 3333
EXPIRATION = 1
MAX_OPERATIONS = 90

bot_active = True
operations_count = 0
last_candle_time = {}
last_update_id = None

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=10,
        )
    except Exception as e:
        print("Telegram:", e)

def check_telegram_commands():
    global bot_active, last_update_id
    try:
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates", timeout=10).json()
        for upd in r.get("result", []):
            uid = upd["update_id"]
            if last_update_id is not None and uid <= last_update_id:
                continue
            last_update_id = uid
            txt = upd.get("message", {}).get("text", "")
            if txt == "/stop":
                bot_active = False
                send_telegram("⛔ BOT DETENIDO")
            elif txt == "/start":
                bot_active = True
                send_telegram("✅ BOT ACTIVADO")
    except Exception as e:
        print(e)

Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()
if not Iq.check_connect():
    raise SystemExit("No se pudo conectar")

send_telegram("🤖 BOT INICIADO")

while True:
    check_telegram_commands()
    if not bot_active:
        time.sleep(2)
        continue
    for pair in PAIRS:
        candles = Iq.get_candles(pair,60,100,time.time())
        if not candles:
            continue
        df = pd.DataFrame([{
            "open": c["open"],
            "close": c["close"],
            "high": c["max"],
            "low": c["min"],
        } for c in candles])
        ct = candles[-1]["from"]
        if last_candle_time.get(pair)==ct:
            continue
        last_candle_time[pair]=ct
        direccion, patron, score = pro_signal(df, aggressive=True)
        if direccion is None:
            continue
        direccion = "put" if direccion=="call" else "call"
        ok, trade_id = Iq.buy(AMOUNT,pair,direccion,EXPIRATION)
        if ok:
            time.sleep(EXPIRATION*60)
            update_result(Iq.check_win_v4(trade_id))
    time.sleep(1)
