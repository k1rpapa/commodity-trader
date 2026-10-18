"""
COT Data Fetcher (19 Assets: Commodities, Equities, Rates, Currencies)
Downloads CFTC Disaggregated & Legacy COT reports (Current week & Historical 3-Year archives).
Calculates Commercial / Non-Commercial / Managed Money Net Positions and 3-Year COT Index.
"""

import os
import io
import csv
import json
import zipfile
import requests
import certifi
from datetime import datetime

TARGET_ASSETS = {
    # 株式指数
    "ES": {"name": "S&P 500 (ES)", "code": "13874A", "source": "dea", "category": "株式指数", "yfinance": "ES=F", "unit": "pt"},
    "NQ": {"name": "NASDAQ 100 (NQ)", "code": "209742", "source": "dea", "category": "株式指数", "yfinance": "NQ=F", "unit": "pt"},
    
    # 貴金属
    "GC": {"name": "ゴールド (GC)", "code": "088691", "source": "disagg", "category": "貴金属", "yfinance": "GC=F", "unit": "USD/oz"},
    "SI": {"name": "シルバー (SI)", "code": "084691", "source": "disagg", "category": "貴金属", "yfinance": "SI=F", "unit": "USD/oz"},
    "PL": {"name": "プラチナ (PL)", "code": "076651", "source": "disagg", "category": "貴金属", "yfinance": "PL=F", "unit": "USD/oz"},
    
    # エネルギー
    "CL": {"name": "原油 WTI (CL)", "code": "067651", "source": "disagg", "category": "エネルギー", "yfinance": "CL=F", "unit": "USD/bbl"},
    "NG": {"name": "天然ガス (NG)", "code": "023651", "source": "disagg", "category": "エネルギー", "yfinance": "NG=F", "unit": "USD/MMBtu"},
    
    # 工業用金属
    "HG": {"name": "銅 (HG)", "code": "085692", "source": "disagg", "category": "工業用金属", "yfinance": "HG=F", "unit": "USD/lb"},
    
    # 穀物・農産物
    "ZS": {"name": "大豆 (ZS)", "code": "005602", "source": "disagg", "category": "穀物・農産物", "yfinance": "ZS=F", "unit": "USc/bu"},
    "ZC": {"name": "トウモロコシ (ZC)", "code": "002602", "source": "disagg", "category": "穀物・農産物", "yfinance": "ZC=F", "unit": "USc/bu"},
    "ZW": {"name": "小麦 (ZW)", "code": "001602", "source": "disagg", "category": "穀物・農産物", "yfinance": "ZW=F", "unit": "USc/bu"},
    
    # ソフトコモディティ
    "SB": {"name": "砂糖 (SB)", "code": "080732", "source": "disagg", "category": "ソフトコモディティ", "yfinance": "SB=F", "unit": "USc/lb"},
    "CT": {"name": "コットン (CT)", "code": "033661", "source": "disagg", "category": "ソフトコモディティ", "yfinance": "CT=F", "unit": "USc/lb"},
    "CC": {"name": "ココア (CC)", "code": "073732", "source": "disagg", "category": "ソフトコモディティ", "yfinance": "CC=F", "unit": "USD/MT"},
    "KC": {"name": "コーヒー (KC)", "code": "083731", "source": "disagg", "category": "ソフトコモディティ", "yfinance": "KC=F", "unit": "USc/lb"},
    
    # 畜産
    "HE": {"name": "豚肉 (HE)", "code": "054642", "source": "disagg", "category": "畜産", "yfinance": "HE=F", "unit": "USc/lb"},
    "LE": {"name": "生牛 (LE)", "code": "057642", "source": "disagg", "category": "畜産", "yfinance": "LE=F", "unit": "USc/lb"},
    
    # 通貨・マクロ・債券
    "DXY": {"name": "ドルインデックス (DXY)", "code": "098662", "source": "dea", "category": "通貨・マクロ", "yfinance": "DX-Y.NYB", "unit": "pt"},
    "ZN": {"name": "米10年債 (ZN)", "code": "043602", "source": "dea", "category": "債券・金利", "yfinance": "ZN=F", "unit": "pt"}
}

CURRENT_DISAGG_URL = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
CURRENT_DEA_URL = "https://www.cftc.gov/dea/newcot/deafut.txt"

HISTORICAL_DISAGG_ZIP = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
HISTORICAL_DEA_ZIP = "https://www.cftc.gov/files/dea/history/deacot{year}.zip"

DATA_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cot_history.json")


def fetch_url(url: str, timeout: int = 35):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, verify=certifi.where(), timeout=timeout)
        if r.status_code == 200:
            return r.content
    except Exception as e:
        print(f"[Warning] Failed to fetch {url}: {e}")
    return None


def parse_disagg_csv(csv_text: str, target_codes: dict):
    # target_codes: {code: sym}
    records = {sym: [] for sym in target_codes.values()}
    reader = csv.reader(io.StringIO(csv_text))
    for row in reader:
        if len(row) > 22:
            code = row[3].strip()
            if code in target_codes:
                sym = target_codes[code]
                try:
                    date_str = row[2].strip()
                    oi = int(row[7].strip() or 0)
                    prod_l = int(row[8].strip() or 0)
                    prod_s = int(row[9].strip() or 0)
                    swap_l = int(row[10].strip() or 0)
                    swap_s = int(row[11].strip() or 0)
                    mm_l = int(row[13].strip() or 0)
                    mm_s = int(row[14].strip() or 0)
                    other_l = int(row[16].strip() or 0)
                    other_s = int(row[17].strip() or 0)

                    comm_l = prod_l + swap_l
                    comm_s = prod_s + swap_s
                    comm_net = comm_l - comm_s

                    noncomm_l = mm_l + other_l
                    noncomm_s = mm_s + other_s
                    noncomm_net = noncomm_l - noncomm_s

                    mm_net = mm_l - mm_s

                    records[sym].append({
                        "date": date_str,
                        "open_interest": oi,
                        "commercials": {"long": comm_l, "short": comm_s, "net": comm_net},
                        "managed_money": {"long": mm_l, "short": mm_s, "net": mm_net},
                        "non_commercials": {"long": noncomm_l, "short": noncomm_s, "net": noncomm_net}
                    })
                except Exception:
                    continue
    return records


def parse_dea_csv(csv_text: str, target_codes: dict):
    # target_codes: {code: sym}
    records = {sym: [] for sym in target_codes.values()}
    reader = csv.reader(io.StringIO(csv_text))
    for row in reader:
        if len(row) > 16:
            code = row[3].strip()
            if code in target_codes:
                sym = target_codes[code]
                try:
                    date_str = row[2].strip()
                    oi = int(row[7].strip() or 0)
                    noncomm_l = int(row[8].strip() or 0)
                    noncomm_s = int(row[9].strip() or 0)
                    comm_l = int(row[11].strip() or 0)
                    comm_s = int(row[12].strip() or 0)

                    comm_net = comm_l - comm_s
                    noncomm_net = noncomm_l - noncomm_s

                    records[sym].append({
                        "date": date_str,
                        "open_interest": oi,
                        "commercials": {"long": comm_l, "short": comm_s, "net": comm_net},
                        "managed_money": {"long": noncomm_l, "short": noncomm_s, "net": noncomm_net},
                        "non_commercials": {"long": noncomm_l, "short": noncomm_s, "net": noncomm_net}
                    })
                except Exception:
                    continue
    return records


def update_and_calculate_indices(force_refresh_history: bool = False):
    all_data = {sym: [] for sym in TARGET_ASSETS}

    if os.path.exists(DATA_CACHE_PATH) and not force_refresh_history:
        try:
            with open(DATA_CACHE_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
                for s in TARGET_ASSETS:
                    if s in cached:
                        all_data[s] = cached[s]
            print("[Info] Loaded existing COT history from cache.")
        except Exception:
            all_data = {sym: [] for sym in TARGET_ASSETS}

    disagg_codes = {info["code"]: sym for sym, info in TARGET_ASSETS.items() if info["source"] == "disagg"}
    dea_codes = {info["code"]: sym for sym, info in TARGET_ASSETS.items() if info["source"] == "dea"}

    need_history = any(len(all_data[s]) < 50 for s in TARGET_ASSETS) or force_refresh_history
    if need_history:
        print("[Info] Downloading 3-year historical COT datasets (Disaggregated + Legacy)...")
        current_year = datetime.now().year
        years = [current_year - i for i in range(3, -1, -1)]

        for yr in years:
            print(f"  Fetching history for {yr}...")
            # 1. Disaggregated History
            disagg_content = fetch_url(HISTORICAL_DISAGG_ZIP.format(year=yr))
            if disagg_content:
                try:
                    z = zipfile.ZipFile(io.BytesIO(disagg_content))
                    txt = z.open(z.namelist()[0]).read().decode("utf-8", errors="ignore")
                    parsed_dis = parse_disagg_csv(txt, disagg_codes)
                    for sym, rows in parsed_dis.items():
                        all_data[sym].extend(rows)
                except Exception as e:
                    print(f"    [Error] Disagg zip {yr}: {e}")

            # 2. Legacy History (for Financials: ES, NQ, DXY, ZN)
            dea_content = fetch_url(HISTORICAL_DEA_ZIP.format(year=yr))
            if dea_content:
                try:
                    z = zipfile.ZipFile(io.BytesIO(dea_content))
                    txt = z.open(z.namelist()[0]).read().decode("utf-8", errors="ignore")
                    parsed_dea = parse_dea_csv(txt, dea_codes)
                    for sym, rows in parsed_dea.items():
                        all_data[sym].extend(rows)
                except Exception as e:
                    print(f"    [Error] Dea zip {yr}: {e}")

    # Fetch current week
    print("[Info] Fetching latest week COT data...")
    curr_disagg = fetch_url(CURRENT_DISAGG_URL)
    if curr_disagg:
        p_dis = parse_disagg_csv(curr_disagg.decode("utf-8", errors="ignore"), disagg_codes)
        for sym, rows in p_dis.items():
            all_data[sym].extend(rows)

    curr_dea = fetch_url(CURRENT_DEA_URL)
    if curr_dea:
        p_dea = parse_dea_csv(curr_dea.decode("utf-8", errors="ignore"), dea_codes)
        for sym, rows in p_dea.items():
            all_data[sym].extend(rows)

    # Deduplicate & Compute 3-Year Rolling COT Index
    results = {}
    for sym in TARGET_ASSETS:
        dedup = {}
        for r in all_data[sym]:
            dedup[r["date"]] = r
        sorted_rows = sorted(dedup.values(), key=lambda x: x["date"])

        for i in range(len(sorted_rows)):
            start_idx = max(0, i - 156)
            window = sorted_rows[start_idx : i + 1]

            comm_nets = [w["commercials"]["net"] for w in window]
            mm_nets = [w["managed_money"]["net"] for w in window]

            c_min, c_max = min(comm_nets), max(comm_nets)
            m_min, m_max = min(mm_nets), max(mm_nets)

            c_curr = sorted_rows[i]["commercials"]["net"]
            m_curr = sorted_rows[i]["managed_money"]["net"]

            c_index = round(((c_curr - c_min) / (c_max - c_min) * 100), 1) if c_max > c_min else 50.0
            m_index = round(((m_curr - m_min) / (m_max - m_min) * 100), 1) if m_max > m_min else 50.0

            sorted_rows[i]["cot_index"] = {
                "commercials": c_index,
                "managed_money": m_index
            }

            if i > 0:
                prev_c = sorted_rows[i-1]["commercials"]["net"]
                prev_m = sorted_rows[i-1]["managed_money"]["net"]
                sorted_rows[i]["weekly_net_change"] = {
                    "commercials": c_curr - prev_c,
                    "managed_money": m_curr - prev_m
                }
            else:
                sorted_rows[i]["weekly_net_change"] = {"commercials": 0, "managed_money": 0}

        results[sym] = sorted_rows

    os.makedirs(os.path.dirname(DATA_CACHE_PATH), exist_ok=True)
    with open(DATA_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[Success] Updated COT data for all 19 assets saved to {DATA_CACHE_PATH}")
    return results


if __name__ == "__main__":
    data = update_and_calculate_indices(force_refresh_history=True)
    for sym, rows in data.items():
        if rows:
            latest = rows[-1]
            print(f"{sym:4s} ({latest['date']}): CommNet={latest['commercials']['net']:+,} (Idx: {latest['cot_index']['commercials']}%) | MMNet={latest['managed_money']['net']:+,} (Idx: {latest['cot_index']['managed_money']}%)")
