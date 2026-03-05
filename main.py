import yfinance as yf
import pandas as pd
import requests

# ==============================
# TELEGRAM CONFIG
# ==============================
TOKEN = "ISI_TOKEN_KAMU"
CHAT_ID = "ISI_CHAT_ID"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ==============================
# LIST 100 SAHAM IDX
# ==============================
stocks = [
"BBCA.JK","BBRI.JK","BMRI.JK","BBNI.JK","TLKM.JK",
"ASII.JK","UNTR.JK","ANTM.JK","ADRO.JK","MDKA.JK",
"GOTO.JK","CPIN.JK","JPFA.JK","BRPT.JK","TPIA.JK",
"EXCL.JK","ISAT.JK","PTBA.JK","SMGR.JK","KLBF.JK",
"ICBP.JK","INDF.JK","INCO.JK","AKRA.JK","TOWR.JK",
"TBIG.JK","ITMG.JK","AMRT.JK","BRMS.JK","DSSA.JK",
"BBTN.JK","BJBR.JK","BJTM.JK","BSDE.JK","PWON.JK",
"CTRA.JK","SMRA.JK","ERAA.JK","MAPI.JK","ACES.JK",
"SIDO.JK","HMSP.JK","GGRM.JK","MIKA.JK","SILO.JK",
"HEAL.JK","MEDC.JK","PGAS.JK","HRUM.JK","INDY.JK",
"DOID.JK","ADHI.JK","WIKA.JK","PTPP.JK","WSKT.JK",
"JSMR.JK","RAJA.JK","ESSA.JK","ELSA.JK","SCMA.JK",
"MNCN.JK","VIVA.JK","FILM.JK","LPPF.JK","RALS.JK",
"MAPA.JK","MPPA.JK","SGER.JK","UNVR.JK","MYOR.JK",
"ROTI.JK","GOOD.JK","AALI.JK","LSIP.JK","SIMP.JK",
"TAPG.JK","DSNG.JK","BISI.JK","MAIN.JK","SRTG.JK",
"IPCM.JK","WINS.JK","BULL.JK","NELY.JK","DEWA.JK",
"BUMA.JK","TOBA.JK","SSMS.JK","GJTL.JK","AUTO.JK",
"IMAS.JK","SMSM.JK","LPKR.JK","DILD.JK","KIJA.JK"
]

# ==============================
# RSI FUNCTION
# ==============================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==============================
# SCAN
# ==============================
bullish = []

for s in stocks:
    try:
        df = yf.download(s, period="6mo", interval="1d", progress=False)

        if len(df) < 60:
            continue

        df["MA20"] = df["Close"].rolling(20).mean()
        df["MA50"] = df["Close"].rolling(50).mean()
        df["VOLAVG"] = df["Volume"].rolling(20).mean()
        df["RSI"] = compute_rsi(df["Close"])

        last = df.iloc[-1]
        prev = df.iloc[-2]

        volume_ok = last["Volume"] > last["VOLAVG"]

        trend = prev["MA20"] < prev["MA50"] and last["MA20"] > last["MA50"]
        reversal = last["RSI"] < 35 and volume_ok

        if volume_ok and (trend or reversal):
            bullish.append(s.replace(".JK",""))

    except:
        continue

# ==============================
# FORMAT TELEGRAM
# ==============================
msg = "STOCKS :\n\n"

if bullish:
    msg += "🟢 BULLISH:\n"
    msg += ", ".join(bullish)
else:
    msg += "🟢 BULLISH:\n\n"

send_telegram(msg)

print("Scan selesai")
