"""
Signal Engine
Combines COT Extremes, 5-Year Seasonal Bias, Options GEX Walls & Regime, and ATR Techncials
to generate comprehensive trading setups and risk-managed trade plans.
"""

import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
COT_PATH = os.path.join(DATA_DIR, "cot_history.json")
GEX_PATH = os.path.join(DATA_DIR, "gex_latest.json")
PRICE_PATH = os.path.join(DATA_DIR, "price_history.json")
SIGNALS_OUTPUT_PATH = os.path.join(DATA_DIR, "signals_latest.json")

# Asset metadata & Seasonality calendar profiles
COMMODITY_PROFILES = {
    "SI": {
        "name": "Silver (銀先物 / CME)",
        "unit": "USD / oz",
        "rakuten_name": "シルバーCFD",
        "seasonal_bias": {
            "10": "秋の調整を経て年末年始ラリーに向けた仕込み期（中立〜強気寄り）",
            "11": "年末買い需要の初動期（強気）",
            "12": "年間高値トライ・季節的強気アノマリー（強気）"
        }
    },
    "NG": {
        "name": "Natural Gas (天然ガス先物 / NYMEX)",
        "unit": "USD / MMBtu",
        "rakuten_name": "天然ガスCFD",
        "seasonal_bias": {
            "10": "秋の在庫注入完了期。暖冬予報で軟調だが、初冬の寒波プレミアムで反発を狙う過渡期",
            "11": "暖房需要期（引き出し期）突入。寒波到来による年内最大の急騰アノマリー（超強気）",
            "12": "厳冬期需要ピーク（高ボラティリティ強気）"
        }
    },
    "ZC": {
        "name": "Corn (トウモロコシ先物 / CBOT)",
        "unit": "USセント / bu",
        "rakuten_name": "コーンCFD",
        "seasonal_bias": {
            "10": "全米収穫圧力（Harvest Pressure）の最終局面。年間最安値をつけやすい底入れゾーン",
            "11": "収穫完了による売り圧力の一巡・自律反発ゾーン（中立〜強気反発）",
            "12": "冬期の南米天候相場（レンジ〜やや強気）"
        }
    },
    "HE": {
        "name": "Lean Hogs (豚肉先物 / CME)",
        "unit": "USセント / lb",
        "rakuten_name": "豚肉先物CFD",
        "seasonal_bias": {
            "10": "秋の過剰出荷が一巡し、年末の感謝祭・クリスマスハム需要に向けた底打ち期（強気転換）",
            "11": "年末実需買いによる底堅い上昇期（強気）",
            "12": "実需納品ピーク（中立）"
        }
    }
}


def load_datasets():
    """Load latest COT, GEX, and Price datasets."""
    cot_data, gex_data, price_data = {}, {}, {}
    if os.path.exists(COT_PATH):
        with open(COT_PATH, "r", encoding="utf-8") as f:
            cot_data = json.load(f)
    if os.path.exists(GEX_PATH):
        with open(GEX_PATH, "r", encoding="utf-8") as f:
            gex_data = json.load(f)
    if os.path.exists(PRICE_PATH):
        with open(PRICE_PATH, "r", encoding="utf-8") as f:
            price_data = json.load(f)
    return cot_data, gex_data, price_data


def evaluate_asset(sym: str, cot_rows: list, gex_info: dict, price_info: dict) -> dict:
    """Evaluate 4 layers for a single commodity and formulate a concrete trade plan."""
    profile = COMMODITY_PROFILES[sym]
    curr_month = str(datetime.now().month)
    seasonal_desc = profile["seasonal_bias"].get(curr_month, "中立的な季節サイクル")

    latest_cot = cot_rows[-1] if cot_rows else {}
    c_idx = latest_cot.get("cot_index", {}).get("commercials", 50.0)
    m_idx = latest_cot.get("cot_index", {}).get("managed_money", 50.0)
    c_net = latest_cot.get("commercials", {}).get("net", 0)
    m_net = latest_cot.get("managed_money", {}).get("net", 0)
    c_chg = latest_cot.get("weekly_net_change", {}).get("commercials", 0)
    m_chg = latest_cot.get("weekly_net_change", {}).get("managed_money", 0)

    # GEX Info
    spot = gex_info.get("spot_price") or (price_info.get("latest", {}).get("close") if price_info else 0)
    zg = gex_info.get("zero_gamma")
    put_wall = gex_info.get("put_wall")
    call_wall = gex_info.get("call_wall")
    regime = gex_info.get("regime", "N/A")
    is_pos_gamma = gex_info.get("is_positive_gamma", True)

    # Price / Techncials
    latest_price = price_info.get("latest", {}) if price_info else {}
    close = latest_price.get("close", spot)
    ema20 = latest_price.get("ema20")
    ema50 = latest_price.get("ema50")
    atr14 = latest_price.get("atr14") or (close * 0.02)
    rsi14 = latest_price.get("rsi14", 50.0)

    # --- SCORING & SETUP DETECTION ---
    score = 0
    signals = []

    # 1. COT Evaluation
    cot_bias = "NEUTRAL"
    if c_idx >= 80 and m_idx <= 25:
        score += 3
        cot_bias = "EXTREME_LONG_SETUP"
        signals.append(f"【COT極限】商業筋COT指数 {c_idx}%(極限買い) ＆ ファンド指数 {m_idx}%(歴史的ショート積層)")
    elif c_idx >= 70:
        score += 1.5
        cot_bias = "LONG_BIAS"
        signals.append(f"【COT追い風】商業筋COT指数 {c_idx}% 買い越し基調")
    elif c_idx <= 20 and m_idx >= 75:
        score -= 3
        cot_bias = "EXTREME_SHORT_SETUP"
        signals.append(f"【COT過熱売り】商業筋COT指数 {c_idx}% ＆ ファンドロング過多 {m_idx}%")

    if c_chg > 0 and m_chg < 0:
        score += 1
        signals.append(f"【スマートマネー先回り】商業筋今週+{c_chg:,}枚買い増し / ファンド売り")

    # 2. Seasonality Evaluation
    signals.append(f"【季節性サイクル】{seasonal_desc}")
    if any(k in seasonal_desc for k in ["強気", "底入れ", "反発"]):
        score += 1.5

    # 3. GEX Evaluation
    if is_pos_gamma:
        signals.append(f"【GEXレジーム】Positive Gamma（ボラティリティ安定、Put壁/ZGによる下値支持が強固）")
        if put_wall and spot >= put_wall:
            score += 1
    else:
        signals.append(f"【GEXレジーム】Negative Gamma（高ボラティリティ、ブレイクアウト加速・スクイーズ急動意警戒）")
        if zg and spot < zg:
            signals.append(f"Spot({spot})がZero-Gamma({zg})を下回っており、上値抵抗として意識")

    # 4. Technical / RSI Oversold/Overbought
    if rsi14 and rsi14 <= 30:
        score += 1.5
        signals.append(f"【テクニカル】日足RSI(14)が {rsi14} と売られすぎ極限域に到達")
    elif rsi14 and rsi14 >= 70:
        score -= 1.5
        signals.append(f"【テクニカル】日足RSI(14)が {rsi14} と買われすぎ域に到達")

    # --- ACTION CLASSIFICATION ---
    action = "NEUTRAL"
    action_label = "様子見 / 監視継続"
    badge_color = "#8e918f"

    if score >= 5.0:
        action = "STRONG_BUY_SETUP"
        action_label = "🔥 高確度ロング・スクイーズ警戒"
        badge_color = "#00e676"
    elif score >= 3.0:
        action = "BUY_PULLBACK"
        action_label = "🟢 押し目買い検討ゾーン"
        badge_color = "#44c265"
    elif score <= -3.0:
        action = "SELL_RALLY"
        action_label = "🔴 戻り売り警戒ゾーン"
        badge_color = "#ff5252"

    # --- CONCRETE TRADE PLAN (SL / TP / LOT CALCULATION) ---
    trade_plan = None
    if action in ["STRONG_BUY_SETUP", "BUY_PULLBACK"]:
        # Entry near current close or Put Wall / ZG
        entry_price = round(close, 3)
        
        # Stop Loss: prioritize Put Wall or ATR
        if put_wall and put_wall < entry_price:
            sl_price = round(min(put_wall - 0.3 * atr14, entry_price - 1.5 * atr14), 3)
        else:
            sl_price = round(entry_price - 2.0 * atr14, 3)
        
        risk_per_unit = max(0.001, entry_price - sl_price)

        # Take Profit: prioritize Call Wall or 2.0 RR
        if call_wall and call_wall > entry_price:
            tp_price = round(call_wall, 3)
        else:
            tp_price = round(entry_price + 2.0 * risk_per_unit, 3)

        reward_per_unit = tp_price - entry_price
        rr_ratio = round(reward_per_unit / risk_per_unit, 2) if risk_per_unit > 0 else 1.0

        trade_plan = {
            "direction": "買い (LONG)",
            "entry_price": entry_price,
            "stop_loss": sl_price,
            "take_profit": tp_price,
            "risk_reward_ratio": rr_ratio,
            "atr_14": round(atr14, 3),
            "put_wall_support": put_wall,
            "call_wall_target": call_wall,
            "risk_distance": round(risk_per_unit, 3),
            "notes": "楽天CFDの指値/逆指値OCO注文にて発注。Put Wall防衛線を背にした損小利大設計。"
        }

    return {
        "symbol": sym,
        "name": profile["name"],
        "unit": profile["unit"],
        "rakuten_name": profile["rakuten_name"],
        "action": action,
        "action_label": action_label,
        "badge_color": badge_color,
        "score": score,
        "spot_price": spot,
        "cot_summary": {
            "commercial_index": c_idx,
            "managed_money_index": m_idx,
            "commercial_net": c_net,
            "managed_money_net": m_net,
            "commercial_weekly_chg": c_chg,
            "managed_money_weekly_chg": m_chg,
            "bias": cot_bias
        },
        "gex_summary": {
            "regime": regime,
            "is_positive": is_pos_gamma,
            "zero_gamma": zg,
            "put_wall": put_wall,
            "call_wall": call_wall
        },
        "technicals": {
            "close": close,
            "ema20": ema20,
            "ema50": ema50,
            "atr14": round(atr14, 3),
            "rsi14": rsi14
        },
        "signals": signals,
        "trade_plan": trade_plan
    }


def generate_all_signals():
    """Run full evaluation and output latest signal state."""
    cot_data, gex_data, price_data = load_datasets()
    results = {}

    for sym in COMMODITY_PROFILES:
        cot_rows = cot_data.get(sym, [])
        gex_info = gex_data.get(sym, {})
        price_info = price_data.get(sym, {})
        
        evaluation = evaluate_asset(sym, cot_rows, gex_info, price_info)
        results[sym] = evaluation

    # Cache output
    with open(SIGNALS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[Success] Generated signals for {len(results)} commodities.")
    return results


if __name__ == "__main__":
    sigs = generate_all_signals()
    for sym, res in sigs.items():
        print(f"\n=== {sym}: {res['name']} ===")
        print(f"Status: {res['action_label']} (Score: {res['score']})")
        print(f"Spot: {res['spot_price']} | PutWall: {res['gex_summary']['put_wall']} | CallWall: {res['gex_summary']['call_wall']}")
        print(f"COT: CommIdx={res['cot_summary']['commercial_index']}%, MMIdx={res['cot_summary']['managed_money_index']}%")
        if res['trade_plan']:
            tp = res['trade_plan']
            print(f"Trade Plan -> Direction: {tp['direction']} | Entry: {tp['entry_price']} | SL: {tp['stop_loss']} | TP: {tp['take_profit']} (RR {tp['risk_reward_ratio']})")
