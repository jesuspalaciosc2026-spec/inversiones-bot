import numpy as np

# ================= LÓGICA ÚNICA: MOMENTO + CONTINUIDAD =================

def vela_momento(vela):
    """Vela de Momento: cuerpo > 60% del rango total, dirección clara"""
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
        return "bajista"
    return None


def vela_continuidad(vela_actual, vela_anterior, direccion_momento):
    """Vela de Continuidad: respeta la dirección y cierra a favor"""
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


# ================= FUNCIÓN DE SEÑAL FINAL =================

def pro_signal(df_m1, df_m5=None, df_htf=None):
    """Solo requiere velas M1; los demás parámetros se mantienen por compatibilidad"""
    min_velas = 3
    if len(df_m1) < min_velas:
        return None, None

    # Tomamos últimas 3 velas: [-3] Momento, [-2] Continuidad, [-1] validación final
    vela_m = df_m1.iloc[-3]
    vela_c = df_m1.iloc[-2]
    vela_confirmacion = df_m1.iloc[-1]

    # 1. PRIMERA CONFIRMACIÓN: Vela de Momento
    direccion = vela_momento(vela_m)
    if not direccion:
        return None, None

    # 2. SEGUNDA CONFIRMACIÓN: Vela de Continuidad
    if not vela_continuidad(vela_c, vela_m, direccion):
        return None, None

    # Validación extra: la última vela no rompe la estructura
    if direccion == "alcista" and vela_confirmacion["close"] < vela_c["close"]:
        return None, None
    if direccion == "bajista" and vela_confirmacion["close"] > vela_c["close"]:
        return None, None

    # Señal final
    return ("call", 1) if direccion == "alcista" else ("put", 1)
