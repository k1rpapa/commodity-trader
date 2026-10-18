"""
Price & Technical Indicator Fetcher
Downloads daily price history from Yahoo Finance for Silver, Natural Gas, Corn, and Lean Hogs.
Calculates 20/50 EMA, ATR(14), RSI(14), 20-day Donchian High/Low, and 5-Year Seasonal Average.
"""

import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

COMMODITY_TICKERS = {
    "SI": "SI=F",
    "NG": "NG=F",
    "ZC": "ZC=F",
    "HE": "HE=F"
}

PRICE_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "price_history.json")


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR)."""
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
    """Calculate Relative Strength Index (RSI)."""
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


def fetch_and_calculate_prices():
    """Fetch 3-year price history and compute technical & seasonal indicators."""
    results = {}
    print("[Info] Fetching price history from Yahoo Finance...")

    for sym, ticker in COMMODITY_TICKERS.items():
        try:
            print(f"  Downloading {sym} ({ticker})...")
            # Fetch 3 years of daily data
            df = yf.download(ticker, period="3y", interval="1d", progress=False)
            if df.empty:
                print(f"[Warning] No data received for {ticker}")
                continue

            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]

            df = df.dropna(subset=["Close"]).copy()
            df["Date"] = df.index.strftime("%Y-%m-%d")

            # Technical Indicators
            df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
            df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
            df["ATR14"] = calculate_atr(df, period=14)
            df["RSI14"] = calculate_rsi(df, period=14)
            df["Donchian_High20"] = df["High"].rolling(window=20).max()
            df["Donchian_Low20"] = df["Low"].rolling(window=20).min()

            # Seasonal Profile (day of year average pattern over 3 years)
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
            print(f"[Success] Processed {len(records)} bars for {sym}. Latest Close: {records[-1]['close']}")

        except Exception as e:
            print(f"[Error] Failed to process prices for {sym}: {e}")

    # Cache
    os.makedirs(os.path.dirname(PRICE_CACHE_PATH), exist_ok=True)
    with open(PRICE_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results


if __name__ == "__main__":
    res = fetch_and_calculate_prices()
    for sym, d in res.items():
        if d["latest"]:
            print(f"{sym}: Close={d['latest']['close']}, EMA20={d['latest']['ema20']}, ATR14={d['latest']['atr14']}, RSI={d['latest']['rsi14']}")
