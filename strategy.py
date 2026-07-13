import numpy as np
import pandas as pd

# ================= CONFIGURACIÓN GLOBAL =================
CONFIG = {
    "ema_periodo": 20,
    "atr_periodo": 14,
    "ventana_niveles": 20,
    "ventana_pruebas": 10,
    "buffer_atr_multiplicador": 1.2,
    "min_velas_htf": 25,
    "min_velas_m5": 15,
    "min_velas_m1": 5
}

# ================= INDICADORES TÉCNICOS =================
def add_indicators(df):
    """Agrega EMA y ATR con manejo seguro de valores"""
    df = df.copy().reset_index(drop=True)
    
    # EMA 20
    df["ema20"] = df["close"].ewm(span=CONFIG["ema_periodo"], adjust=False).mean()
    
    # Cálculo correcto de TR y ATR
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift(1))
    low_close = abs(df["low"] - df["close"].shift(1))
    
    df["tr"] = np.maximum(high_low, np.maximum(high_close, low_close))
    df["atr"] = df["tr"].rolling(CONFIG["atr_periodo"], min_periods=CONFIG["atr_periodo"]).mean()
    
    # Rellenar valores NaN iniciales
    df["atr"] = df["atr"].bfill()
    
    return df

# ================= DETECTAR NIVELES SOPORTE/RESISTENCIA (HTF) =================
def get_zone(df_htf):
    """Obtiene niveles con validación de datos suficientes"""
    if len(df_htf) < CONFIG["min_velas_htf"]:
        return None, None
    
    df_ventana = df_htf.tail(CONFIG["ventana_niveles"])
    resistance = df_ventana["high"].max()
    support = df_ventana["low"].min()
    
    return round(support, 5), round(resistance, 5)

# ================= VERIFICAR DOBLE PRUEBA DE NIVEL =================
def double_touch(df_m5, nivel, es_soporte=True):
    """Valida al menos 2 toques sin romper el nivel definitivamente"""
    if len(df_m5) < CONFIG["min_velas_m5"]:
        return False
    
    conteo_toques = 0
    umbral_ruptura = nivel * 0.0015  # 0.15% de margen para no confundir ruido
    
    for i in range(-CONFIG["ventana_pruebas"], 0):
        vela = df_m5.iloc[i]
        
        if es_soporte:
            if vela["low"] <= nivel and vela["close"] > (nivel - umbral_ruptura):
                conteo_toques += 1
        else:
            if vela["high"] >= nivel and vela["close"] < (nivel + umbral_ruptura):
                conteo_toques += 1
    
    return conteo_toques >= 2

# ================= CONFIRMACIÓN DE VELA Y TENDENCIA =================
def confirmation(df_m1, direccion, df_htf=None):
    """Confirma dirección y tendencia mayor para evitar señales contrarias"""
    if len(df_m1) < CONFIG["min_velas_m1"]:
        return False
    
    ultima = df_m1.iloc[-1]
    vela_anterior = df_m1.iloc[-2]
    
    # Confirmación básica de color
    valido = False
    if direccion == "call":
        valido = (ultima["close"] > ultima["open"]) and (ultima["close"] > vela_anterior["close"])
    elif direccion == "put":
        valido = (ultima["close"] < ultima["open"]) and (ultima["close"] < vela_anterior["close"])
    
    # Filtrar por tendencia del marco mayor (opcional pero muy efectivo)
    if valido and df_htf is not None and len(df_htf) >= CONFIG["min_velas_htf"]:
        ema_htf = df_htf["ema20"].iloc[-1]
        precio_htf = df_htf["close"].iloc[-1]
        
        if direccion == "call" and precio_htf < ema_htf:
            return False
        if direccion == "put" and precio_htf > ema_htf:
            return False
    
    return valido

# ================= FUNCIÓN PRINCIPAL DE SEÑAL =================
def pro_signal(df_m1, df_m5, df_htf):
    """
    Genera señal validada:
    - Retorna: (direccion, expiracion_en_minutos) o (None, None)
    """
    # Validar que todos los marcos tengan datos suficientes
    if any([
        len(df_htf) < CONFIG["min_velas_htf"],
        len(df_m5) < CONFIG["min_velas_m5"],
        len(df_m1) < CONFIG["min_velas_m1"]
    ]):
        return None, None
    
    # Agregar indicadores si no existen
    if "ema20" not in df_htf.columns:
        df_htf = add_indicators(df_htf)
    if "atr" not in df_m1.columns:
        df_m1 = add_indicators(df_m1)
    
    # Obtener niveles y datos
    soporte, resistencia = get_zone(df_htf)
    if soporte is None or resistencia is None:
        return None, None
    
    precio_actual = round(df_m1["close"].iloc[-1], 5)
    atr_actual = df_m1["atr"].iloc[-1]
    
    if np.isnan(atr_actual) or atr_actual <= 0:
        return None, None
    
    margen_nivel = atr_actual * CONFIG["buffer_atr_multiplicador"]
    
    # ================== SEÑAL DE COMPRA (CALL) ==================
    if abs(precio_actual - soporte) <= margen_nivel:
        if double_touch(df_m5, soporte, es_soporte=True):
            if confirmation(df_m1, "call", df_htf):
                return "call", 3
    
    # ================== SEÑAL DE VENTA (PUT) ==================
    if abs(precio_actual - resistencia) <= margen_nivel:
        if double_touch(df_m5, resistencia, es_soporte=False):
            if confirmation(df_m1, "put", df_htf):
                return "put", 3
    
    return None, None
