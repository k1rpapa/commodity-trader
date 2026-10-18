"""
COT Data Fetcher
Downloads CFTC Disaggregated Futures COT reports (both current week and historical years)
Extracts positions for Silver, Natural Gas, Corn, and Lean Hogs.
Calculates Commercial / Managed Money Net Positions and 3-Year COT Index.
"""

import os
import io
import csv
import json
import zipfile
import requests
import certifi
import pandas as pd
from datetime import datetime

TARGET_COMMODITIES = {
    "SI": {
        "name": "Silver (銀)",
        "code": "084691",
        "exchange": "COMMODITY EXCHANGE INC.",
        "yfinance_symbol": "SI=F"
    },
    "NG": {
        "name": "Natural Gas (天然ガス)",
        "code": "023651",
        "exchange": "NEW YORK MERCANTILE EXCHANGE",
        "yfinance_symbol": "NG=F"
    },
    "ZC": {
        "name": "Corn (トウモロコシ)",
        "code": "002602",
        "exchange": "CHICAGO BOARD OF TRADE",
        "yfinance_symbol": "ZC=F"
    },
    "HE": {
        "name": "Lean Hogs (豚肉)",
        "code": "054642",
        "exchange": "CHICAGO MERCANTILE EXCHANGE",
        "yfinance_symbol": "HE=F"
    }
}

CURRENT_WEEK_URL = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
HISTORICAL_ZIP_TEMPLATE = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
DATA_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cot_history.json")


def fetch_current_week():
    """Fetch current week's disaggregated COT data."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(CURRENT_WEEK_URL, headers=headers, verify=certifi.where(), timeout=25)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[Warning] Failed to fetch current week COT: {e}")
        return None


def fetch_historical_year(year: int):
    """Fetch annual historical zip file from CFTC and return CSV text."""
    url = HISTORICAL_ZIP_TEMPLATE.format(year=year)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, verify=certifi.where(), timeout=35)
        if resp.status_code != 200:
            return None
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        first_file = z.namelist()[0]
        with z.open(first_file) as f:
            return f.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[Warning] Failed to fetch historical COT for {year}: {e}")
        return None


def parse_cot_csv(csv_text: str):
    """Parse CFTC disaggregated CSV text and filter for target commodities."""
    records = {sym: [] for sym in TARGET_COMMODITIES}
    target_codes = {info["code"]: sym for sym, info in TARGET_COMMODITIES.items()}

    reader = csv.reader(io.StringIO(csv_text))
    header = None

    for row in reader:
        if not row:
            continue
        if header is None and ("Market_and_Exchange_Names" in row[0] or "Market" in row[0]):
            header = [h.strip() for h in row]
            continue
        
        # Check market code (usually column 3)
        if len(row) > 3:
            code = row[3].strip()
            if code in target_codes:
                sym = target_codes[code]
                try:
                    date_str = row[2].strip()  # YYYY-MM-DD
                    open_interest = int(row[7].strip() or 0)
                    
                    prod_long = int(row[8].strip() or 0)
                    prod_short = int(row[9].strip() or 0)
                    swap_long = int(row[10].strip() or 0)
                    swap_short = int(row[11].strip() or 0)
                    
                    mm_long = int(row[13].strip() or 0)
                    mm_short = int(row[14].strip() or 0)
                    mm_spread = int(row[15].strip() or 0)
                    
                    other_long = int(row[16].strip() or 0)
                    other_short = int(row[17].strip() or 0)
                    
                    nonrept_long = int(row[21].strip() or 0)
                    nonrept_short = int(row[22].strip() or 0)

                    # Changes
                    chg_oi = int(row[55].strip() or 0) if len(row) > 55 else 0
                    chg_prod_long = int(row[56].strip() or 0) if len(row) > 56 else 0
                    chg_prod_short = int(row[57].strip() or 0) if len(row) > 57 else 0
                    chg_swap_long = int(row[58].strip() or 0) if len(row) > 58 else 0
                    chg_swap_short = int(row[59].strip() or 0) if len(row) > 59 else 0
                    chg_mm_long = int(row[61].strip() or 0) if len(row) > 61 else 0
                    chg_mm_short = int(row[62].strip() or 0) if len(row) > 62 else 0

                    comm_long = prod_long + swap_long
                    comm_short = prod_short + swap_short
                    comm_net = comm_long - comm_short

                    noncomm_long = mm_long + other_long
                    noncomm_short = mm_short + other_short
                    noncomm_net = noncomm_long - noncomm_short

                    mm_net = mm_long - mm_short

                    records[sym].append({
                        "date": date_str,
                        "open_interest": open_interest,
                        "producers": {"long": prod_long, "short": prod_short, "chg_long": chg_prod_long, "chg_short": chg_prod_short},
                        "swap_dealers": {"long": swap_long, "short": swap_short, "chg_long": chg_swap_long, "chg_short": chg_swap_short},
                        "commercials": {"long": comm_long, "short": comm_short, "net": comm_net},
                        "managed_money": {"long": mm_long, "short": mm_short, "spread": mm_spread, "net": mm_net, "chg_long": chg_mm_long, "chg_short": chg_mm_short},
                        "non_commercials": {"long": noncomm_long, "short": noncomm_short, "net": noncomm_net},
                        "other_reportables": {"long": other_long, "short": other_short},
                        "non_reportable": {"long": nonrept_long, "short": nonrept_short}
                    })
                except Exception as ex:
                    # Ignore malformed row
                    continue

    return records


def update_and_calculate_indices(force_refresh_history: bool = False):
    """
    Fetch historical and latest COT data, merge, sort, compute 3-Year COT Index,
    and save to DATA_CACHE_PATH.
    """
    all_data = {sym: [] for sym in TARGET_COMMODITIES}
    
    # Check if cache exists
    if os.path.exists(DATA_CACHE_PATH) and not force_refresh_history:
        try:
            with open(DATA_CACHE_PATH, "r", encoding="utf-8") as f:
                all_data = json.load(f)
            print("[Info] Loaded existing COT history from cache.")
        except Exception:
            all_data = {sym: [] for sym in TARGET_COMMODITIES}

    # If cache has less than 50 rows per symbol, backfill history (last 3-4 years)
    need_history = any(len(all_data[s]) < 50 for s in TARGET_COMMODITIES) or force_refresh_history
    if need_history:
        print("[Info] Downloading 3-year historical COT datasets from CFTC...")
        current_year = datetime.now().year
        # CFTC history covers e.g. 2023, 2024, 2025, 2026
        years = [current_year - i for i in range(3, -1, -1)]
        for yr in years:
            print(f"  Fetching year {yr}...")
            yr_txt = fetch_historical_year(yr)
            if yr_txt:
                parsed = parse_cot_csv(yr_txt)
                for sym, rows in parsed.items():
                    all_data[sym].extend(rows)

    # Fetch latest week
    print("[Info] Fetching current week COT data...")
    curr_txt = fetch_current_week()
    if curr_txt:
        curr_parsed = parse_cot_csv(curr_txt)
        for sym, rows in curr_parsed.items():
            all_data[sym].extend(rows)

    # Deduplicate and sort by date
    results = {}
    for sym in TARGET_COMMODITIES:
        dedup = {}
        for r in all_data[sym]:
            dedup[r["date"]] = r
        sorted_rows = sorted(dedup.values(), key=lambda x: x["date"])
        
        # Calculate Rolling 3-Year COT Index (156 weeks)
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
            
            # Weekly net change
            if i > 0:
                prev_c = sorted_rows[i-1]["commercials"]["net"]
                prev_m = sorted_rows[i-1]["managed_money"]["net"]
                sorted_rows[i]["weekly_net_change"] = {
                    "commercials": c_curr - prev_c,
                    "managed_money": m_curr - prev_m
                }
            else:
                sorted_rows[i]["weekly_net_change"] = {
                    "commercials": 0,
                    "managed_money": 0
                }

        results[sym] = sorted_rows

    # Save to cache
    os.makedirs(os.path.dirname(DATA_CACHE_PATH), exist_ok=True)
    with open(DATA_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[Success] Updated COT data saved to {DATA_CACHE_PATH}")
    return results


if __name__ == "__main__":
    data = update_and_calculate_indices(force_refresh_history=True)
    for sym, rows in data.items():
        if rows:
            latest = rows[-1]
            print(f"--- {sym}: {TARGET_COMMODITIES[sym]['name']} ---")
            print(f"Latest Date: {latest['date']}")
            print(f"Commercials Net: {latest['commercials']['net']:,} (COT Index: {latest['cot_index']['commercials']}%)")
            print(f"Managed Money Net: {latest['managed_money']['net']:,} (COT Index: {latest['cot_index']['managed_money']}%)")
            print(f"Weekly Net Chg: Comm: {latest['weekly_net_change']['commercials']:+,} | MM: {latest['weekly_net_change']['managed_money']:+,}")
