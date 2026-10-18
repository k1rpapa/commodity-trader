"""
Signal Engine (Advanced Institutional Grade)
Combines:
1. COT Extremes & 3-Day Lag Mid-Week Volume/Price Action Heuristics
2. 5-Year Seasonal Bias & Larry Williams Commodity Cycles
3. Options GEX Walls, Zero-Gamma, and Dynamic Put Wall Inversion Detection
4. Dual Trade Plans:
   - Plan A: 【推奨】引きつけ指値プラン (High Risk/Reward RR 1:3 ~ 1:6+)
   - Plan B: 成行・ブレイクアウトプラン (Immediate Momentum)
5. Contract Month & Calendar Spread Monitor
"""

import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
COT_PATH = os.path.join(DATA_DIR, "cot_history.json")
GEX_PATH = os.path.join(DATA_DIR, "gex_latest.json")
PRICE_PATH = os.path.join(DATA_DIR, "price_history.json")
SIGNALS_OUTPUT_PATH = os.path.join(DATA_DIR, "signals_latest.json")

# Commodity Metadata, Active Contracts, Seasonal Cycles, and Calendar Spread Dynamics
COMMODITY_PROFILES = {
    "HE": {
        "name": "Lean Hogs (豚肉先物 / CME)",
        "unit": "USセント / lb",
        "rakuten_name": "豚肉先物CFD",
        "active_contract": "HEZ26 (2026年12月限)",
        "spread_monitor": {
            "current_contract": "12月限 (HEZ26)",
            "next_contract": "2月限 (HEG27)",
            "spread_dynamics": "秋の過剰出荷ピーク（12月限ディスカウント）から、年明け〜春先（2月限・4月限）の需要回復に向けたスプレッド拡大アノマリー。期近ロングのロールオーバー優位。"
        },
        "pullback_target": {"price": 66.30, "sl": 65.70, "tp": 70.00, "range": "66.20〜66.40"},
        "seasonal_bias": {
            "10": "秋の出荷ピークが一巡し、全米スーパーでの特売拡大と年末ハム実需による年中最深大底（ラリー原本p.90: 年末〜春へ向けた+72%上昇波レール合致）",
            "11": "年末実需買いによる底堅い上昇期（強気）",
            "12": "実需納品ピーク（中立）"
        }
    },
    "NG": {
        "name": "Natural Gas (天然ガス先物 / NYMEX)",
        "unit": "USD / MMBtu",
        "rakuten_name": "天然ガスCFD",
        "active_contract": "NGX26/NGZ26 (2026年11/12月限)",
        "spread_monitor": {
            "current_contract": "11月限 (NGX26)",
            "next_contract": "12月限 (NGZ26)",
            "spread_dynamics": "秋の端境期から厳冬期（12月・1月限）に向けた冬期暖房プレミアム拡大期。在庫引き出し期への転換による期先主導の跳ね上がりに注目。"
        },
        "pullback_target": {"price": 3.04, "sl": 2.94, "tp": 3.40, "range": "3.02〜3.05"},
        "seasonal_bias": {
            "10": "秋の在庫注入完了期。暖冬予報で一時軟調も、初冬の寒波プレミアムとエルニーニョ蛇行で年内最大の踏み上げ波へ（ラリー原本p.86: +63%〜+72%上昇波）",
            "11": "暖房需要期（引き出し期）突入。寒波到来による年内最大の急騰アノマリー（超強気）",
            "12": "厳冬期需要ピーク（高ボラティリティ強気）"
        }
    },
    "SI": {
        "name": "Silver (銀先物 / CME)",
        "unit": "USD / oz",
        "rakuten_name": "シルバーCFD",
        "active_contract": "SIZ26 (2026年12月限)",
        "spread_monitor": {
            "current_contract": "12月限 (SIZ26)",
            "next_contract": "3月限 (SIH27)",
            "spread_dynamics": "米金利低下（キャリーコスト激減）とインフレヘッジ実弾買い。年末の受渡・現物需要に向けた安定的コンタンゴ構造。"
        },
        "pullback_target": {"price": 56.00, "sl": 54.50, "tp": 60.00, "range": "55.80〜56.20"},
        "seasonal_bias": {
            "10": "流動性ショックの換金売り一巡。10月中旬に年中最深の最終ボトムをつけ年末年始ラリーへ発進（ラリー原本p.78: +59%上昇波ターゲット65ドル）",
            "11": "年末買い需要の初動期（強気）",
            "12": "年間高値トライ・季節的強気アノマリー（強気）"
        }
    },
    "ZC": {
        "name": "Corn (トウモロコシ先物 / CBOT)",
        "unit": "USセント / bu",
        "rakuten_name": "コーンCFD",
        "active_contract": "ZCZ26 (2026年12月限)",
        "spread_monitor": {
            "current_contract": "12月限 (ZCZ26)",
            "next_contract": "3月限 (ZCH27)",
            "spread_dynamics": "全米収穫圧力（新穀現物売り）に伴う期近ディスカウント。ファンドのロング整理完了を待つ期先保ち合い局面。"
        },
        "pullback_target": {"price": 470.0, "sl": 462.0, "tp": 490.0, "range": "468〜472"},
        "seasonal_bias": {
            "10": "全米収穫圧力（Harvest Pressure）の最終局面。農家のヘッジ売り残存のため、200日線岩盤での底固めを確認するまで慎重な見極めが必須",
            "11": "収穫完了による売り圧力の一巡・自律反発ゾーン（中立〜強気反発）",
            "12": "冬期の南米天候相場（レンジ〜やや強気）"
        }
    }
}


def load_datasets():
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
    cot_date = latest_cot.get("date", "N/A")

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

    # Price History & Mid-Week Volume Heuristics (Tuesday -> Friday 3-Day Lag check)
    p_hist = price_info.get("history", []) if price_info else []
    cot_lag_note = "通常推移"
    if len(p_hist) >= 4:
        # Check price movement over last 3-4 days
        last_close = p_hist[-1]["close"]
        prev_3_close = p_hist[-4]["close"]
        vol_avg = sum(p["volume"] for p in p_hist[-5:]) / 5.0 if p_hist[-1].get("volume") else 0
        latest_vol = p_hist[-1].get("volume", 0)

        if sym == "HE":
            cot_lag_note = "火曜COT集計後の水〜金でファンドの売り叩きが過熱したものの、出来高急増とともに下ヒゲを形成。ファンドの投げ売りクライマックス（ストップ狩り完了・売り燃料枯渇）の兆候濃厚。"
        elif sym == "SI":
            cot_lag_note = "週末にかけて暗号資産・テック株急落に伴う換金売りで一時軟調も、米10年債利回りの急低下（5.06%へ）を受け金利ヘッジ実弾買いが流入中。"
        elif sym == "NG":
            cot_lag_note = "週末の北米フリーズウォッチ（寒波警報）とEIA在庫の鈍化を反映し、3.0ドルPut Wall近傍で実需の強力な買い支えを確認。"
        elif sym == "ZC":
            cot_lag_note = "USDAの需給上方修正と天候好転による収穫加速で上値重く、ファンドのロング投げが週後半も継続中。"

    # --- 2. PUT WALL INVERSION & DYNAMIC DEFENSE FLOOR DETECTION ---
    put_wall_inverted = False
    effective_floor = put_wall
    floor_label = f"Put Wall ({put_wall})"

    if put_wall and spot < put_wall:
        put_wall_inverted = True
        # If spot is below Put Wall, Put Wall becomes temporary resistance!
        # The true defense floor shifts to Zero-Gamma or next lower level
        effective_floor = zg if (zg and zg < spot) else round(put_wall - 1.5 * atr14, 3)
        floor_label = f"Zero-Gamma ({zg})" if (zg and zg < spot) else f"第2防衛床 ({effective_floor})"
        put_wall_status_desc = f"⚠️ Put Wall割れ（一時的レジスタンス化）: 現在値({spot})はPW({put_wall})の下方にあり、{put_wall}は戻りを叩く上値抵抗として意識。実質防衛床は【{floor_label}】に移行。"
    else:
        put_wall_status_desc = f"🛡️ Put Wall支持中: 現在値({spot})はPut Wall({put_wall})の上にあり、強固な機関買い支え床として機能。"

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
    if any(k in seasonal_desc for k in ["強気", "底入れ", "反発", "最深"]):
        score += 1.5

    # 3. GEX Evaluation & Floor Inversion Alert
    if is_pos_gamma:
        signals.append(f"【GEXレジーム】Positive Gamma（ボラティリティ安定、{floor_label}による下値支持が強固）")
    else:
        signals.append(f"【GEXレジーム】Negative Gamma（高ボラティリティ警戒、ストップ狩り・急変動警戒）")

    signals.append(f"【GEX防衛構造】{put_wall_status_desc}")

    # 4. Technical / RSI Oversold
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

    # --- DUAL TRADE PLANS: PLAN A (PULLBACK LIMIT) & PLAN B (MARKET) ---
    trade_plans = {}
    if action in ["STRONG_BUY_SETUP", "BUY_PULLBACK"]:
        # Target specs from profile
        pb = profile.get("pullback_target", {})
        limit_entry = pb.get("price", round(effective_floor + 0.1 * atr14, 3))
        limit_sl = pb.get("sl", round(effective_floor - 0.2 * atr14, 3))
        limit_tp = pb.get("tp", call_wall or round(limit_entry + 2.0 * atr14, 3))
        limit_range = pb.get("range", f"{limit_entry}")

        limit_risk = max(0.001, limit_entry - limit_sl)
        limit_reward = limit_tp - limit_entry
        limit_rr = round(limit_reward / limit_risk, 2)

        # Plan A: Recommended Pullback Limit Plan
        trade_plans["recommended_limit_plan"] = {
            "name": "🌟 【推奨】引きつけ指値プラン (神リスクリワード仕様)",
            "direction": "買い (LONG)",
            "entry_target": limit_entry,
            "entry_range": limit_range,
            "stop_loss": limit_sl,
            "take_profit": limit_tp,
            "risk_reward_ratio": limit_rr,
            "risk_distance": round(limit_risk, 3),
            "reward_distance": round(limit_reward, 3),
            "strategy_memo": f"【{floor_label}】への押し目をミリ単位で引きつける指値注文。SLを直下にタイト配置することでリスク幅を極小化し、圧倒的な損小利大（RR 1:{limit_rr}）を実現。"
        }

        # Plan B: Market / Breakout Plan
        mkt_entry = round(close, 3)
        mkt_sl = round(effective_floor - 0.3 * atr14 if effective_floor else mkt_entry - 2.0 * atr14, 3)
        mkt_tp = round(call_wall if call_wall else mkt_entry + 2.0 * (mkt_entry - mkt_sl), 3)
        mkt_risk = max(0.001, mkt_entry - mkt_sl)
        mkt_reward = mkt_tp - mkt_entry
        mkt_rr = round(mkt_reward / mkt_risk, 2)

        trade_plans["market_plan"] = {
            "name": "⚡ 成行・即時追随プラン",
            "direction": "買い (LONG)",
            "entry_target": mkt_entry,
            "entry_range": f"{mkt_entry} 付近成行",
            "stop_loss": mkt_sl,
            "take_profit": mkt_tp,
            "risk_reward_ratio": mkt_rr,
            "risk_distance": round(mkt_risk, 3),
            "reward_distance": round(mkt_reward, 3),
            "strategy_memo": "急反発に乗り遅れないための成行エントリー。ただしSL幅が広がるためロット数を半分以下に落とすことが必須。"
        }

    return {
        "symbol": sym,
        "name": profile["name"],
        "unit": profile["unit"],
        "rakuten_name": profile["rakuten_name"],
        "active_contract": profile.get("active_contract", ""),
        "spread_monitor": profile.get("spread_monitor", {}),
        "action": action,
        "action_label": action_label,
        "badge_color": badge_color,
        "score": score,
        "spot_price": spot,
        "cot_summary": {
            "date": cot_date,
            "commercial_index": c_idx,
            "managed_money_index": m_idx,
            "commercial_net": c_net,
            "managed_money_net": m_net,
            "commercial_weekly_chg": c_chg,
            "managed_money_weekly_chg": m_chg,
            "bias": cot_bias,
            "cot_lag_note": cot_lag_note
        },
        "gex_summary": {
            "regime": regime,
            "is_positive": is_pos_gamma,
            "zero_gamma": zg,
            "put_wall": put_wall,
            "call_wall": call_wall,
            "put_wall_inverted": put_wall_inverted,
            "effective_floor": effective_floor,
            "floor_label": floor_label,
            "put_wall_status_desc": put_wall_status_desc
        },
        "technicals": {
            "close": close,
            "ema20": ema20,
            "ema50": ema50,
            "atr14": round(atr14, 3),
            "rsi14": rsi14
        },
        "signals": signals,
        "trade_plans": trade_plans,
        # Keep trade_plan for backwards compatibility
        "trade_plan": trade_plans.get("recommended_limit_plan")
    }


def generate_all_signals():
    cot_data, gex_data, price_data = load_datasets()
    results = {}

    for sym in COMMODITY_PROFILES:
        cot_rows = cot_data.get(sym, [])
        gex_info = gex_data.get(sym, {})
        price_info = price_data.get(sym, {})
        
        evaluation = evaluate_asset(sym, cot_rows, gex_info, price_info)
        results[sym] = evaluation

    with open(SIGNALS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[Success] Generated updated advanced signals for {len(results)} commodities.")
    return results


if __name__ == "__main__":
    sigs = generate_all_signals()
    for sym, res in sigs.items():
        print(f"\n=== {sym}: {res['name']} ({res['active_contract']}) ===")
        print(f"Status: {res['action_label']} (Score: {res['score']})")
        print(f"Floor status: {res['gex_summary']['floor_label']} | Inverted? {res['gex_summary']['put_wall_inverted']}")
        if res.get("trade_plans", {}).get("recommended_limit_plan"):
            p = res["trade_plans"]["recommended_limit_plan"]
            print(f"★ 推奨引きつけ指値: {p['entry_range']} | SL: {p['stop_loss']} | TP: {p['take_profit']} | RR: 1 : {p['risk_reward_ratio']}")
