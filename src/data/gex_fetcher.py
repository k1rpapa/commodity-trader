"""
GEX Data Fetcher (19 Assets)
Extracts live Options GEX data from https://k1rpapa.github.io/options-gex-radar/
for all 19 assets (excluding JPY).
"""

import os
import re
import json
import requests
import certifi
from bs4 import BeautifulSoup

COMMODITY_PAGES = {
    # 株式指数
    "ES": {"url": "https://k1rpapa.github.io/options-gex-radar/es.html", "name": "S&P 500 (ES)"},
    "NQ": {"url": "https://k1rpapa.github.io/options-gex-radar/nq.html", "name": "NASDAQ 100 (NQ)"},
    
    # 貴金属
    "GC": {"url": "https://k1rpapa.github.io/options-gex-radar/gc.html", "name": "ゴールド (GC)"},
    "SI": {"url": "https://k1rpapa.github.io/options-gex-radar/index.html", "name": "シルバー (SI)"},
    "PL": {"url": "https://k1rpapa.github.io/options-gex-radar/pl.html", "name": "プラチナ (PL)"},
    
    # エネルギー
    "CL": {"url": "https://k1rpapa.github.io/options-gex-radar/cl.html", "name": "原油 WTI (CL)"},
    "NG": {"url": "https://k1rpapa.github.io/options-gex-radar/ng.html", "name": "天然ガス (NG)"},
    
    # 工業用金属
    "HG": {"url": "https://k1rpapa.github.io/options-gex-radar/hg.html", "name": "銅 (HG)"},
    
    # 穀物・農産物
    "ZS": {"url": "https://k1rpapa.github.io/options-gex-radar/zs.html", "name": "大豆 (ZS)"},
    "ZC": {"url": "https://k1rpapa.github.io/options-gex-radar/zc.html", "name": "トウモロコシ (ZC)"},
    "ZW": {"url": "https://k1rpapa.github.io/options-gex-radar/zw.html", "name": "小麦 (ZW)"},
    
    # ソフトコモディティ
    "SB": {"url": "https://k1rpapa.github.io/options-gex-radar/sb.html", "name": "砂糖 (SB)"},
    "CT": {"url": "https://k1rpapa.github.io/options-gex-radar/ct.html", "name": "コットン (CT)"},
    "CC": {"url": "https://k1rpapa.github.io/options-gex-radar/cc.html", "name": "ココア (CC)"},
    "KC": {"url": "https://k1rpapa.github.io/options-gex-radar/kc.html", "name": "コーヒー (KC)"},
    
    # 畜産
    "HE": {"url": "https://k1rpapa.github.io/options-gex-radar/he.html", "name": "豚肉 (HE)"},
    "LE": {"url": "https://k1rpapa.github.io/options-gex-radar/le.html", "name": "生牛 (LE)"},
    
    # 通貨・マクロ・債券
    "DXY": {"url": "https://k1rpapa.github.io/options-gex-radar/dxy.html", "name": "ドルインデックス (DXY)"},
    "ZN": {"url": "https://k1rpapa.github.io/options-gex-radar/zn.html", "name": "米10年債 (ZN)"}
}

GEX_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "gex_latest.json")


def fetch_gex_data():
    results = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    print(f"[Info] Fetching GEX data for {len(COMMODITY_PAGES)} assets from options-gex-radar...")

    for sym, info in COMMODITY_PAGES.items():
        url = info["url"]
        try:
            resp = requests.get(url, headers=headers, verify=certifi.where(), timeout=15)
            if resp.status_code != 200:
                print(f"[Warning] Failed to fetch {sym} GEX page: HTTP {resp.status_code}")
                continue

            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # 1. Regime
            regime_el = soup.find("div", class_="regime-badge")
            regime_text = regime_el.text.strip() if regime_el else "NEUTRAL"
            is_positive = "POSITIVE" in regime_text.upper()

            # 2. Alert Banner
            alert_title_el = soup.find("div", class_="zg-alert-title")
            alert_title = alert_title_el.text.strip() if alert_title_el else ""
            alert_content_el = soup.find("div", class_="zg-alert-content")
            alert_text = alert_content_el.text.strip().replace("\n", " ") if alert_content_el else ""

            # 3. Spot & Zero Gamma
            m_spot = re.search(r'Spot:\s*([0-9.]+)', html)
            spot_price = float(m_spot.group(1)) if m_spot else None

            m_zg = re.search(r'Zero-Gamma:\s*([0-9.]+)', html)
            zero_gamma = float(m_zg.group(1)) if m_zg else None

            # 4. AI summary content
            ai_div = soup.find("div", class_="ai-content")
            ai_summary = ai_div.text.strip() if ai_div else ""

            # 5. Robust Put Wall and Call Wall Extraction
            put_wall = None
            call_wall = None

            m_put = re.search(r'Put Wall(?:\s*\(サポート\))?[^\d]{1,15}([0-9]+(?:\.[0-9]+)?)', ai_summary)
            if m_put:
                put_wall = float(m_put.group(1))

            m_call = re.search(r'Call Wall(?:\s*\(レジスタンス\))?[^\d]{1,15}([0-9]+(?:\.[0-9]+)?)', ai_summary)
            if m_call:
                call_wall = float(m_call.group(1))

            if put_wall is None:
                m_put_fallback = re.search(r'Put Wall[^\d]{1,15}([0-9]+(?:\.[0-9]+)?)', html)
                if m_put_fallback:
                    put_wall = float(m_put_fallback.group(1))

            if call_wall is None:
                m_call_fallback = re.search(r'Call Wall[^\d]{1,15}([0-9]+(?:\.[0-9]+)?)', html)
                if m_call_fallback:
                    call_wall = float(m_call_fallback.group(1))

            sub_info = soup.find("div", class_="chart-sub-info")
            as_of_info = sub_info.text.strip() if sub_info else ""

            results[sym] = {
                "symbol": sym,
                "name": info["name"],
                "url": url,
                "as_of_info": as_of_info,
                "spot_price": spot_price,
                "zero_gamma": zero_gamma,
                "put_wall": put_wall,
                "call_wall": call_wall,
                "regime": regime_text,
                "is_positive_gamma": is_positive,
                "alert_title": alert_title,
                "alert_text": alert_text,
                "ai_summary": ai_summary[:350]
            }

        except Exception as e:
            print(f"[Error] Exception parsing GEX for {sym}: {e}")

    os.makedirs(os.path.dirname(GEX_CACHE_PATH), exist_ok=True)
    with open(GEX_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[Success] Extracted and cached GEX data for {len(results)} assets.")
    return results


if __name__ == "__main__":
    res = fetch_gex_data()
    for sym, d in res.items():
        print(f"{sym:4s}: Spot={d['spot_price']} | ZG={d['zero_gamma']} | Put={d['put_wall']} | Call={d['call_wall']} | Reg={'POS' if d['is_positive_gamma'] else 'NEG'}")
