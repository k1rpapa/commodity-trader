"""
Signal Engine (19 Assets Institutional Grade)
Evaluates COT Extremes, 5-Year Seasonal Bias, Options GEX Walls, and ATR Risk Management
for all 19 assets (Commodities, Equities, Macro).
Generates Dual Trade Plans (Recommended Pullback Limit vs Market).
"""

import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
COT_PATH = os.path.join(DATA_DIR, "cot_history.json")
GEX_PATH = os.path.join(DATA_DIR, "gex_latest.json")
PRICE_PATH = os.path.join(DATA_DIR, "price_history.json")
SIGNALS_OUTPUT_PATH = os.path.join(DATA_DIR, "signals_latest.json")

ASSET_PROFILES = {
    # --- 株式指数 ---
    "ES": {
        "name": "S&P 500 (ES)", "category": "株式指数", "unit": "pt", "rakuten_name": "米国S&P500 CFD",
        "active_contract": "ESZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "翌年3月限", "spread_dynamics": "配当落ちと短期金利を織り込んだ順ざや（コンタンゴ）構造。"},
        "seasonal_bias": {"10": "10月後半は歴史的年末ラリー（Year-End Rally）の起点となる季節的底入れ期", "11": "年間最高勝率の強気トレンド期", "12": "サンタクロース・ラリー"}
    },
    "NQ": {
        "name": "NASDAQ 100 (NQ)", "category": "株式指数", "unit": "pt", "rakuten_name": "米国NASDAQ100 CFD",
        "active_contract": "NQZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "翌年3月限", "spread_dynamics": "大型ハイテク企業の決算期を跨ぐボラティリティプレミアム。"},
        "seasonal_bias": {"10": "秋の調整一巡後の年末モメンタム加速期", "11": "感謝祭・ブラックフライデー売上期待の強気波", "12": "年末ラリー"}
    },
    
    # --- 貴金属 ---
    "GC": {
        "name": "ゴールド (GC)", "category": "貴金属", "unit": "USD/oz", "rakuten_name": "金（ゴールド）CFD",
        "active_contract": "GCZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "2月限", "spread_dynamics": "実質金利低下と各国中銀の現物買いによる低コスト保有構造。"},
        "seasonal_bias": {"10": "秋の保ち合いから年末〜1月のアノマリー（インド婚礼・中国春節需要）へ", "11": "現物需要立ち上がり（強気）", "12": "年間高値トライ"}
    },
    "SI": {
        "name": "シルバー (SI)", "category": "貴金属", "unit": "USD/oz", "rakuten_name": "銀（シルバー）CFD",
        "active_contract": "SIZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "3月限", "spread_dynamics": "米金利低下とインフレヘッジ実需。受渡期に向けた安定コンタンゴ。"},
        "seasonal_bias": {"10": "10月中旬に最終ボトムをつけ年末年始+59%上昇波（ラリー原本p.78）", "11": "年末買い需要の初動期（強気）", "12": "年間高値トライ"}
    },
    "PL": {
        "name": "プラチナ (PL)", "category": "貴金属", "unit": "USD/oz", "rakuten_name": "プラチナCFD",
        "active_contract": "PLF27 (1月限)",
        "spread_monitor": {"current_contract": "1月限", "next_contract": "4月限", "spread_dynamics": "自動車触媒・水素産業需要。ゴールドに対する割安是正スプレッド。"},
        "seasonal_bias": {"10": "秋の底固め期", "11": "産業用需要の引き取り期（やや強気）", "12": "年明けラリー準備期"}
    },

    # --- エネルギー ---
    "CL": {
        "name": "原油 WTI (CL)", "category": "エネルギー", "unit": "USD/bbl", "rakuten_name": "WTI原油CFD",
        "active_contract": "CLX26 (11月限)",
        "spread_monitor": {"current_contract": "11月限", "next_contract": "12月限", "spread_dynamics": "地政学プレミアムとOPEC+減産政策。期近プレミアム（バックワーデーション）監視。"},
        "seasonal_bias": {"10": "秋の製油所定期修理（メンテナンス）による需要減退から冬期暖房油需要への転換", "11": "冬期暖房需要プレミアム", "12": "年末ポジション調整"}
    },
    "NG": {
        "name": "天然ガス (NG)", "category": "エネルギー", "unit": "USD/MMBtu", "rakuten_name": "天然ガスCFD",
        "active_contract": "NGX26/NGZ26 (11/12月限)",
        "spread_monitor": {"current_contract": "11月限", "next_contract": "12月限", "spread_dynamics": "在庫注入期から引き出し期への冬期暖房プレミアム拡大。"},
        "seasonal_bias": {"10": "初冬の寒波プレミアムとエルニーニョ蛇行による年内最大の踏み上げ波（ラリー原本p.86）", "11": "暖房需要期（超強気）", "12": "厳冬期需要ピーク"}
    },

    # --- 工業用金属 ---
    "HG": {
        "name": "銅 (HG)", "category": "工業用金属", "unit": "USD/lb", "rakuten_name": "銅CFD",
        "active_contract": "HGZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "3月限", "spread_dynamics": "世界電化・AIデータセンター送電網需要。LME・COMEX在庫逼迫度。"},
        "seasonal_bias": {"10": "世界景況感と中国政策期待の綱引き（レンジ）", "11": "年末実需引き取り（やや強気）", "12": "新年度設備投資アノマリー"}
    },

    # --- 穀物・農産物 ---
    "ZS": {
        "name": "大豆 (ZS)", "category": "穀物・農産物", "unit": "USc/bu", "rakuten_name": "大豆CFD",
        "active_contract": "ZSX26 (11月限)",
        "spread_monitor": {"current_contract": "11月限", "next_contract": "1月限", "spread_dynamics": "全米収穫進行（期近売り圧力）と南米（ブラジル）作付け天候相場。"},
        "seasonal_bias": {"10": "収穫圧力ピークによる年間最安値形成期", "11": "収穫完了による自律反発ゾーン", "12": "南米天候相場"}
    },
    "ZC": {
        "name": "トウモロコシ (ZC)", "category": "穀物・農産物", "unit": "USc/bu", "rakuten_name": "コーンCFD",
        "active_contract": "ZCZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "3月限", "spread_dynamics": "新穀収穫加速に伴う現物売り圧力。200日線岩盤での底固め。"},
        "seasonal_bias": {"10": "全米収穫圧力（Harvest Pressure）の最終局面。農家のヘッジ売り一巡待ち", "11": "自律反発期", "12": "レンジ保ち合い"}
    },
    "ZW": {
        "name": "小麦 (ZW)", "category": "穀物・農産物", "unit": "USc/bu", "rakuten_name": "小麦CFD",
        "active_contract": "ZWZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "3月限", "spread_dynamics": "黒海・豪州生産動向と北半球冬小麦の作付け天候。"},
        "seasonal_bias": {"10": "冬小麦作付け進捗と秋の安値圏（底堅い）", "11": "天候プレミアム（やや強気）", "12": "越冬期保ち合い"}
    },

    # --- ソフトコモディティ ---
    "SB": {
        "name": "砂糖 (SB)", "category": "ソフトコモディティ", "unit": "USc/lb", "rakuten_name": "砂糖CFD",
        "active_contract": "SBH27 (3月限)",
        "spread_monitor": {"current_contract": "3月限", "next_contract": "5月限", "spread_dynamics": "ブラジル・インドのサトウキビ圧搾期終了に伴う端境期供給。"},
        "seasonal_bias": {"10": "ブラジル製糖終盤による秋の保ち合い", "11": "インド減産懸念・エタノール需要（やや強気）", "12": "供給逼迫期"}
    },
    "CT": {
        "name": "コットン (CT)", "category": "ソフトコモディティ", "unit": "USc/lb", "rakuten_name": "綿花CFD",
        "active_contract": "CTZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "3月限", "spread_dynamics": "米南部・テキサス収穫進捗と世界アパレル需要。"},
        "seasonal_bias": {"10": "収穫期による上値の重い保ち合い", "11": "収穫完了による下げ止まり", "12": "年末需要回復"}
    },
    "CC": {
        "name": "ココア (CC)", "category": "ソフトコモディティ", "unit": "USD/MT", "rakuten_name": "ココアCFD",
        "active_contract": "CCZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "3月限", "spread_dynamics": "西アフリカ（コートジボワール・ガーナ）のメインクロップ収穫状況。"},
        "seasonal_bias": {"10": "秋のメインクロップ初動。歴史的減産懸念からの底値買い需要（強気）", "11": "収穫ピーク判明期", "12": "クリスマス菓子需要"}
    },
    "KC": {
        "name": "コーヒー (KC)", "category": "ソフトコモディティ", "unit": "USc/lb", "rakuten_name": "コーヒーCFD",
        "active_contract": "KCZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "3月限", "spread_dynamics": "ブラジルの開花期降雨量と認証在庫の低水準維持。"},
        "seasonal_bias": {"10": "開花期天候不順リスクを織り込む反発期（強気）", "11": "結実期天候チェック", "12": "欧米冬期消費ピーク"}
    },

    # --- 畜産 ---
    "HE": {
        "name": "豚肉 (HE)", "category": "畜産", "unit": "USc/lb", "rakuten_name": "豚肉先物CFD",
        "active_contract": "HEZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "2月限", "spread_dynamics": "秋の出荷ピークから年末ハム・春先需要回復へのスプレッド拡大アノマリー。"},
        "seasonal_bias": {"10": "全米スーパー特売拡大と年末ハム実需による年中最深大底（ラリー原本p.90: +72%上昇波）", "11": "年末実需買い（強気）", "12": "実需納品ピーク"}
    },
    "LE": {
        "name": "生牛 (LE)", "category": "畜産", "unit": "USc/lb", "rakuten_name": "生牛CFD",
        "active_contract": "LEZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "2月限", "spread_dynamics": "全米牛飼育頭数の歴史的低水準とパッカーマージン。"},
        "seasonal_bias": {"10": "秋の需要安定期。高値圏維持による商業筋の買い支え（底堅い）", "11": "感謝祭・冬期ステーキ需要", "12": "年末高アノマリー"}
    },

    # --- 通貨・マクロ・債券 ---
    "DXY": {
        "name": "ドルインデックス (DXY)", "category": "通貨・マクロ", "unit": "pt", "rakuten_name": "米ドル指数",
        "active_contract": "DXZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "3月限", "spread_dynamics": "米FRB金融政策と日欧金利差を反映した通貨バスケット構造。"},
        "seasonal_bias": {"10": "秋の米金利見通し修正によるレンジ展開", "11": "年末リパトリエーション（ややドル買い）", "12": "年末ドル需要一巡"}
    },
    "ZN": {
        "name": "米10年債 (ZN)", "category": "債券・金利", "unit": "pt", "rakuten_name": "米国10年国債",
        "active_contract": "ZNZ26 (12月限)",
        "spread_monitor": {"current_contract": "12月限", "next_contract": "3月限", "spread_dynamics": "国債入札動向とインフレ期待。質への逃避（Flight to Quality）買い。"},
        "seasonal_bias": {"10": "市場波乱時の最強の安全資産逃避先（利回り低下＝債券価格急反発）", "11": "利下げ織り込み進行", "12": "年末ポートフォリオ調整"}
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
    profile = ASSET_PROFILES[sym]
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

    # Put Wall Inversion Check
    put_wall_inverted = False
    effective_floor = put_wall
    floor_label = f"Put Wall ({put_wall})"

    if put_wall and spot < put_wall:
        put_wall_inverted = True
        effective_floor = zg if (zg and zg < spot) else round(put_wall - 1.5 * atr14, 3)
        floor_label = f"Zero-Gamma ({zg})" if (zg and zg < spot) else f"第2防衛床 ({effective_floor})"
        put_wall_status_desc = f"Put Wall割れ（一時的レジスタンス化）: 現在値({spot})はPW({put_wall})の下方にあり、{put_wall}は戻りを叩く上値抵抗として意識。実質防衛床は【{floor_label}】に移行。"
    else:
        put_wall_status_desc = f"Put Wall支持中: 現在値({spot})はPut Wall({put_wall})の上にあり、強固な機関買い支え床として機能。"

    # Scoring
    score = 0
    signals = []

    # 1. COT Evaluation
    cot_bias = "NEUTRAL"
    if c_idx >= 80 and m_idx <= 25:
        score += 3.5
        cot_bias = "EXTREME_LONG_SETUP"
        signals.append(f"【COT極限】商業筋COT指数 {c_idx}%(極限買い) ＆ ファンド指数 {m_idx}%(歴史的ショート積層)")
    elif c_idx >= 75:
        score += 2.0
        cot_bias = "LONG_BIAS"
        signals.append(f"【COT追い風】商業筋COT指数 {c_idx}% 買い越し基調")
    elif c_idx <= 20 and m_idx >= 75:
        score -= 3.0
        cot_bias = "EXTREME_SHORT_SETUP"
        signals.append(f"【COT過熱売り】商業筋COT指数 {c_idx}% ＆ ファンドロング過多 {m_idx}%")

    if c_chg > 0 and m_chg < 0:
        score += 1.0
        signals.append(f"【スマートマネー先回り】商業筋今週+{c_chg:,}枚買い増し / ファンド売り")

    # 2. Seasonality Evaluation
    signals.append(f"【季節性サイクル】{seasonal_desc}")
    if any(k in seasonal_desc for k in ["強気", "底入れ", "反発", "最深", "上昇波"]):
        score += 1.5

    # 3. GEX Evaluation
    if is_pos_gamma:
        signals.append(f"【GEXレジーム】Positive Gamma（ボラティリティ安定、{floor_label}による下値支持が強固）")
    else:
        signals.append(f"【GEXレジーム】Negative Gamma（高ボラティリティ警戒、ストップ狩り・急変動警戒）")

    signals.append(f"【GEX防衛構造】{put_wall_status_desc}")

    # 4. Technical / RSI
    if rsi14 and rsi14 <= 30:
        score += 1.5
        signals.append(f"【テクニカル】日足RSI(14)が {rsi14} と売られすぎ極限域に到達")
    elif rsi14 and rsi14 >= 70:
        score -= 1.5
        signals.append(f"【テクニカル】日足RSI(14)が {rsi14} と買われすぎ域に到達")

    # Classification
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

    # Dual Trade Plans
    trade_plans = {}
    if action in ["STRONG_BUY_SETUP", "BUY_PULLBACK"]:
        # Pullback Limit Plan
        if effective_floor and effective_floor < spot:
            limit_entry = round(effective_floor + 0.15 * atr14, 3)
            limit_sl = round(effective_floor - 0.2 * atr14, 3)
        else:
            limit_entry = round(spot - 0.5 * atr14, 3)
            limit_sl = round(spot - 1.8 * atr14, 3)

        limit_tp = round(call_wall if (call_wall and call_wall > limit_entry) else limit_entry + 2.5 * atr14, 3)
        limit_risk = max(0.001, limit_entry - limit_sl)
        limit_reward = max(0.001, limit_tp - limit_entry)
        limit_rr = round(limit_reward / limit_risk, 2)

        trade_plans["recommended_limit_plan"] = {
            "name": "🌟 【推奨】引きつけ指値プラン (神リスクリワード仕様)",
            "direction": "買い (LONG)",
            "entry_target": limit_entry,
            "entry_range": f"{limit_entry} 付近",
            "stop_loss": limit_sl,
            "take_profit": limit_tp,
            "risk_reward_ratio": limit_rr,
            "risk_distance": round(limit_risk, 3),
            "reward_distance": round(limit_reward, 3),
            "strategy_memo": f"【{floor_label}】への押し目をミリ単位で引きつける指値。SLを直下にタイト配置し、RR 1:{limit_rr} の損小利大を強制執行。"
        }

        # Market Plan
        mkt_entry = round(close, 3)
        mkt_sl = round(effective_floor - 0.3 * atr14 if (effective_floor and effective_floor < mkt_entry) else mkt_entry - 2.0 * atr14, 3)
        mkt_tp = round(call_wall if (call_wall and call_wall > mkt_entry) else mkt_entry + 2.0 * (mkt_entry - mkt_sl), 3)
        mkt_risk = max(0.001, mkt_entry - mkt_sl)
        mkt_reward = max(0.001, mkt_tp - mkt_entry)
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
            "strategy_memo": "急反発に乗り遅れないための成行エントリー。SL幅が広がるためロット数を半分以下に落とすことが必須。"
        }

    return {
        "symbol": sym,
        "name": profile["name"],
        "category": profile.get("category", "コモディティ"),
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
            "bias": cot_bias
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
        "trade_plan": trade_plans.get("recommended_limit_plan")
    }


def generate_all_signals():
    cot_data, gex_data, price_data = load_datasets()
    results = {}

    for sym in ASSET_PROFILES:
        cot_rows = cot_data.get(sym, [])
        gex_info = gex_data.get(sym, {})
        price_info = price_data.get(sym, {})
        
        evaluation = evaluate_asset(sym, cot_rows, gex_info, price_info)
        results[sym] = evaluation

    with open(SIGNALS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[Success] Generated signals for all {len(results)} assets.")
    return results


if __name__ == "__main__":
    generate_all_signals()
