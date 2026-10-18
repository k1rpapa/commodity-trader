"""
Price & Technical Indicator Fetcher (19 Assets)
Downloads daily price history from Yahoo Finance for all 19 assets (commodities & macro).
Calculates 20/50 EMA, ATR(14), RSI(14), 20-day Donchian High/Low, and 5-Year Seasonal Average.
"""

import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

COMMODITY_TICKERS = {
    # 株式指数
    "ES": "ES=F",
    "NQ": "NQ=F",
    
    # 貴金属
    "GC": "GC=F",
    "SI": "SI=F",
    "PL": "PL=F",
    
    # エネルギー
    "CL": "CL=F",
    "NG": "NG=F",
    
    # 工業用金属
    "HG": "HG=F",
    
    # 穀物・農産物
    "ZS": "ZS=F",
    "ZC": "ZC=F",
    "ZW": "ZW=F",
    
    # ソフトコモディティ
    "SB": "SB=F",
    "CT": "CT=F",
    "CC": "CC=F",
    "KC": "KC=F",
    
    # 畜産
    "HE": "HE=F",
    "LE": "LE=F",
    
    # 通貨・マクロ・債券
    "DXY": "DX-Y.NYB",
    "ZN": "ZN=F"
}

PRICE_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "price_history.json")


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


def fetch_and_calculate_prices():
    results = {}
    print(f"[Info] Fetching 3-year price history for {len(COMMODITY_TICKERS)} assets from Yahoo Finance...")

    for sym, ticker in COMMODITY_TICKERS.items():
        try:
            df = yf.download(ticker, period="3y", interval="1d", progress=False)
            if df.empty:
                print(f"[Warning] No data received for {ticker}")
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]

            df = df.dropna(subset=["Close"]).copy()
            df["Date"] = df.index.strftime("%Y-%m-%d")

            df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
            df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
            df["ATR14"] = calculate_atr(df, period=14)
            df["RSI14"] = calculate_rsi(df, period=14)
            df["Donchian_High20"] = df["High"].rolling(window=20).max()
            df["Donchian_Low20"] = df["Low"].rolling(window=20).min()

            df["DayOfYear"] = df.index.dayofyear
            seasonal_map = df.groupby("DayOfYear")["Close"].mean().to_dict()

            records = []
            for idx, row in df.iterrows():
                d_str = row["Date"]
                c_val = float(row["Close"])
                doy = idx.dayofyear
                s_avg = float(seasonal_map.get(doy, c_val))
                
                records.append({
                    "date": d_str,
                    "open": round(float(row["Open"]), 4),
                    "high": round(float(row["High"]), 4),
                    "low": round(float(row["Low"]), 4),
                    "close": round(c_val, 4),
                    "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
                    "ema20": round(float(row["EMA20"]), 4) if not pd.isna(row["EMA20"]) else None,
                    "ema50": round(float(row["EMA50"]), 4) if not pd.isna(row["EMA50"]) else None,
                    "atr14": round(float(row["ATR14"]), 4) if not pd.isna(row["ATR14"]) else None,
                    "rsi14": round(float(row["RSI14"]), 1) if not pd.isna(row["RSI14"]) else None,
                    "donchian_high20": round(float(row["Donchian_High20"]), 4) if not pd.isna(row["Donchian_High20"]) else None,
                    "donchian_low20": round(float(row["Donchian_Low20"]), 4) if not pd.isna(row["Donchian_Low20"]) else None,
                    "seasonal_avg": round(s_avg, 4)
                })

            results[sym] = {
                "symbol": sym,
                "ticker": ticker,
                "latest": records[-1] if records else None,
                "history": records
            }
            print(f"  [OK] {sym:4s} ({ticker}): {len(records)} bars. Latest Close: {records[-1]['close']}")

        except Exception as e:
            print(f"  [Error] {sym}: {e}")

    os.makedirs(os.path.dirname(PRICE_CACHE_PATH), exist_ok=True)
    with open(PRICE_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results


if __name__ == "__main__":
    fetch_and_calculate_prices()
