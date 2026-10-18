"""
GEX Data Fetcher
Extracts live Options GEX data from https://k1rpapa.github.io/options-gex-radar/
for Silver (SI), Natural Gas (NG), Corn (ZC), and Lean Hogs (HE).
"""

import os
import re
import json
import requests
import certifi
from bs4 import BeautifulSoup

COMMODITY_PAGES = {
    "SI": {
        "url": "https://k1rpapa.github.io/options-gex-radar/index.html",
        "name": "Silver (銀)"
    },
    "NG": {
        "url": "https://k1rpapa.github.io/options-gex-radar/ng.html",
        "name": "Natural Gas (天然ガス)"
    },
    "ZC": {
        "url": "https://k1rpapa.github.io/options-gex-radar/zc.html",
        "name": "Corn (トウモロコシ)"
    },
    "HE": {
        "url": "https://k1rpapa.github.io/options-gex-radar/he.html",
        "name": "Lean Hogs (豚肉)"
    }
}

GEX_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "gex_latest.json")


def fetch_gex_data():
    """Fetch and parse GEX metrics from live options-gex-radar pages."""
    results = {}
    headers = {"User-Agent": "Mozilla/5.0"}

    for sym, info in COMMODITY_PAGES.items():
        url = info["url"]
        try:
            resp = requests.get(url, headers=headers, verify=certifi.where(), timeout=20)
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

            # Search in AI summary text first
            m_put = re.search(r'Put Wall(?:\s*\(サポート\))?[^\d]{1,15}([0-9]+(?:\.[0-9]+)?)', ai_summary)
            if m_put:
                put_wall = float(m_put.group(1))

            m_call = re.search(r'Call Wall(?:\s*\(レジスタンス\))?[^\d]{1,15}([0-9]+(?:\.[0-9]+)?)', ai_summary)
            if m_call:
                call_wall = float(m_call.group(1))

            # Fallback search anywhere in html if not matched
            if put_wall is None:
                m_put_fallback = re.search(r'Put Wall[^\d]{1,15}([0-9]+(?:\.[0-9]+)?)', html)
                if m_put_fallback:
                    put_wall = float(m_put_fallback.group(1))

            if call_wall is None:
                m_call_fallback = re.search(r'Call Wall[^\d]{1,15}([0-9]+(?:\.[0-9]+)?)', html)
                if m_call_fallback:
                    call_wall = float(m_call_fallback.group(1))

            # 6. Expiry and As of
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
            print(f"[Success] Extracted GEX for {sym}: Spot={spot_price}, ZG={zero_gamma}, PutWall={put_wall}, CallWall={call_wall}")

        except Exception as e:
            print(f"[Error] Exception parsing GEX for {sym}: {e}")

    # Cache results
    os.makedirs(os.path.dirname(GEX_CACHE_PATH), exist_ok=True)
    with open(GEX_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results


if __name__ == "__main__":
    res = fetch_gex_data()
    print("\nSummary of GEX Data:")
    for sym, d in res.items():
        print(f"{sym}: Spot={d['spot_price']}, ZG={d['zero_gamma']}, PutWall={d['put_wall']}, CallWall={d['call_wall']}, Regime={d['regime']}")
