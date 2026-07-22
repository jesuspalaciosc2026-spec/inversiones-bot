import numpy as np

# ================= DEFINICIÓN DE VELAS (REGLAS INTACTAS) =================

def vela_momento(vela):
    """Vela de Momento: cuerpo > 60% del rango, dirección clara"""
    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["high"] - vela["low"]
    if rango == 0:
        return None
    
    es_alcista = vela["close"] > vela["open"]
    es_bajista = vela["close"] < vela["open"]
    cuerpo_fuerte = cuerpo > (rango * 0.6)

    if es_alcista and cuerpo_fuerte:
        return "alcista"
    if es_bajista and cuerpo_fuerte:
        return None
    return None


def vela_continuidad(vela_actual, vela_anterior, direccion_momento):
    """Vela de Continuidad: sigue la dirección y cierra a favor"""
    cuerpo = abs(vela_actual["close"] - vela_actual["open"])
    rango = vela_actual["high"] - vela_actual["low"]
    if rango == 0:
        return False

    if direccion_momento == "alcista":
        return (vela_actual["close"] > vela_actual["open"] 
                and vela_actual["close"] > vela_anterior["close"]
                and cuerpo > (rango * 0.4))
    
    if direccion_momento == "bajista":
        return (vela_actual["close"] < vela_actual["open"] 
                and vela_actual["close"] < vela_anterior["close"]
                and cuerpo > (rango * 0.4))
    
    return False


# ================= SEÑAL CONFIRMADA EN M15 + M5 =================

def pro_signal(df_m1, df_m5, df_m15):
    """
    Orden de confirmación:
    1. M15: Vela de Momento (fuerza estructural)
    2. M5: Vela de Continuidad (sigue la dirección)
    3. M1: Validación final sin romper la estructura
    """
    # Verificar que haya suficientes velas en cada marco
    if len(df_m15) < 2 or len(df_m5) < 2 or len(df_m1) < 1:
        return None, None

    # 1️⃣ PRIMERA CONFIRMACIÓN: Vela de Momento en M15
    vela_m15 = df_m15.iloc[-1]
    direccion = vela_momento(vela_m15)
    if not direccion:
        return None, None

    # 2️⃣ SEGUNDA CONFIRMACIÓN: Vela de Continuidad en M5
    vela_m5_actual = df_m5.iloc[-1]
    vela_m5_anterior = df_m5.iloc[-2]
    if not vela_continuidad(vela_m5_actual, vela_m5_anterior, direccion):
        return None, None

    # 3️⃣ VALIDACIÓN FINAL EN M1: no rompe la dirección
    vela_m1 = df_m1.iloc[-1]
    if direccion == "alcista" and vela_m1["close"] < vela_m5_actual["close"]:
        return None, None
    if direccion == "bajista" and vela_m1["close"] > vela_m5_actual["close"]:
        return None, None

    # ✅ SEÑAL APROBADA
    return ("call", 1) if direccion == "alcista" else ("put", 1)
