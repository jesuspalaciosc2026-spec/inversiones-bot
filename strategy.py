import pandas as pd

def is_lateral(df):
    last=df.tail(20)
    return (last["high"].max()-last["low"].min())<0.002

def ruptura_lateral(df):
    last,prev=df.iloc[-1],df.iloc[-2]
    cuerpo=abs(last["close"]-last["open"]); rango=last["high"]-last["low"]
    if cuerpo>rango*0.6:
        if last["close"]>prev["high"]: return "call"
        if last["close"]<prev["low"]: return "put"
    return None

def zona_repetida(df):
    p=df["close"].iloc[-1]
    return sum(abs(df["close"].iloc[i]-p)<0.0003 for i in range(-15,-1))>=3

def vela_limpia(df):
    c=df.iloc[-1]
    cuerpo=abs(c["close"]-c["open"])
    return (c["high"]-max(c["open"],c["close"])<=cuerpo and
            min(c["open"],c["close"])-c["low"]<=cuerpo)

def continuidad(df,d):
    a,b=df.iloc[-2],df.iloc[-3]
    return (a["close"]>a["open"] or b["close"]>b["open"]) if d=="call" else (a["close"]<a["open"] or b["close"]<b["open"])

def tendencia_alcista(df):
    h,l=df["high"].tail(5).values,df["low"].tail(5).values
    return h[0]<h[-1] and l[0]<l[-1]

def tendencia_bajista(df):
    h,l=df["high"].tail(5).values,df["low"].tail(5).values
    return h[0]>h[-1] and l[0]>l[-1]

def pullback_alcista(df): return sum(v["close"]>v["open"] for _,v in df.tail(4).iterrows())>=2
def pullback_bajista(df): return sum(v["close"]<v["open"] for _,v in df.tail(4).iterrows())>=2
def vela_fuerte_alcista(df):
    c=df.iloc[-1]; cuerpo=abs(c["close"]-c["open"]);r=c["high"]-c["low"]; return c["close"]>c["open"] and cuerpo>r*0.6
def vela_fuerte_bajista(df):
    c=df.iloc[-1]; cuerpo=abs(c["close"]-c["open"]);r=c["high"]-c["low"]; return c["close"]<c["open"] and cuerpo>r*0.6

def generate_signal(df):
    if len(df)<30:return None
    if tendencia_bajista(df) and pullback_alcista(df) and vela_fuerte_bajista(df):
        return {"direction":"put","score":4}
    if tendencia_alcista(df) and pullback_bajista(df) and vela_fuerte_alcista(df):
        return {"direction":"call","score":4}
    if not is_lateral(df): return None
    d=ruptura_lateral(df)
    if not d or zona_repetida(df) or not continuidad(df,d): return None
    s=5 if vela_limpia(df) else 4
    return {"direction":d,"score":s}

def pro_signal(df, aggressive=False):
    s=generate_signal(df)
    if s is None: return None,None,0
    return s["direction"],"CONTINUACION",s["score"]

def update_result(result):
    print(f"Resultado operación: {result}")
