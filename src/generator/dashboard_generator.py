"""
Dashboard Generator (Institutional Upgrade)
Builds the advanced responsive HTML dashboard in docs/index.html with:
1. Dual Trade Plan Display:
   - Plan A: 🌟 【推奨】引きつけ指値プラン (神リスクリワード仕様 RR 1:3 ~ 1:6)
   - Plan B: ⚡ 成行・即時追随プラン
2. Put Wall Inversion & Dynamic Defense Floor Warnings
3. COT 3-Day Lag Mid-Week Volume & Price Action Heuristics
4. Active Contract Month & Calendar Spread Dynamics Monitor
"""

import os
import json
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")

COT_PATH = os.path.join(DATA_DIR, "cot_history.json")
GEX_PATH = os.path.join(DATA_DIR, "gex_latest.json")
PRICE_PATH = os.path.join(DATA_DIR, "price_history.json")
SIGNALS_PATH = os.path.join(DATA_DIR, "signals_latest.json")


def load_all_data():
    with open(COT_PATH, "r", encoding="utf-8") as f:
        cot = json.load(f)
    with open(GEX_PATH, "r", encoding="utf-8") as f:
        gex = json.load(f)
    with open(PRICE_PATH, "r", encoding="utf-8") as f:
        prices = json.load(f)
    with open(SIGNALS_PATH, "r", encoding="utf-8") as f:
        signals = json.load(f)
    return cot, gex, prices, signals


def generate_dashboard():
    cot_data, gex_data, price_data, signals_data = load_all_data()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M JST")

    symbols = ["HE", "NG", "SI", "ZC"]
    sym_icons = {"HE": "🐷", "NG": "🔥", "SI": "🥈", "ZC": "🌽"}

    frontend_data = {}
    for sym in symbols:
        c_rows = cot_data.get(sym, [])
        p_hist = price_data.get(sym, {}).get("history", [])
        sig = signals_data.get(sym, {})
        gex_info = gex_data.get(sym, {})

        frontend_data[sym] = {
            "name": sig.get("name", sym),
            "rakuten_name": sig.get("rakuten_name", ""),
            "unit": sig.get("unit", ""),
            "active_contract": sig.get("active_contract", ""),
            "spread_monitor": sig.get("spread_monitor", {}),
            "signal": sig,
            "gex": gex_info,
            "cot": c_rows,
            "price": p_hist[-300:] if len(p_hist) > 300 else p_hist
        }

    html_content = f"""<!DOCTYPE html>
<html lang="ja" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>クオンツ・コモディティ戦略レーダー (COT × 季節性 × GEX × スプレッド)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            background-color: #0d1017;
            color: #ffffff;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.5;
        }}
        .nav-tabs {{
            background: #151822;
            padding: 10px 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid #232734;
            align-items: center;
        }}
        .brand-title {{
            font-size: 16px;
            font-weight: 800;
            color: #f9ab00;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-right: 15px;
        }}
        .tab-btn {{
            background: #1c202d;
            color: #c4c7c5;
            border: 1px solid #2b3040;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        .tab-btn:hover {{ background: #282e40; color: #fff; }}
        .tab-btn.active {{ background: #0b57d0; color: #fff; border-color: #3b82f6; box-shadow: 0 0 12px rgba(11,87,208,0.4); }}
        .header-meta {{
            margin-left: auto;
            font-size: 12px;
            color: #8e918f;
            font-family: 'JetBrains Mono', monospace;
        }}
        .container {{
            max-width: 1700px;
            margin: 0 auto;
            padding: 24px 20px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}
        .tab-pane {{ display: none; }}
        .tab-pane.active {{ display: flex; flex-direction: column; gap: 24px; }}
        
        .top-row-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }}
        @media (min-width: 1100px) {{
            .top-row-grid {{ grid-template-columns: 1.25fr 0.75fr; }}
        }}

        .card {{
            background: #141721;
            border: 1px solid #232734;
            border-radius: 12px;
            padding: 20px;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            border-bottom: 1px solid #232734;
            padding-bottom: 12px;
        }}
        .card-title {{
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
        }}

        /* Dual Trade Plan Styling */
        .plans-container {{
            display: flex;
            flex-direction: column;
            gap: 14px;
            margin-top: 14px;
        }}
        .plan-card-recommended {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(11, 87, 208, 0.15) 100%);
            border: 1.5px solid #10b981;
            border-radius: 10px;
            padding: 18px;
            position: relative;
            box-shadow: 0 4px 20px rgba(16, 185, 129, 0.1);
        }}
        .plan-card-market {{
            background: #1a1e2b;
            border: 1px solid #2e3549;
            border-radius: 10px;
            padding: 14px 18px;
        }}
        .plan-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .plan-title-rec {{
            font-size: 16px;
            font-weight: 800;
            color: #34d399;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .plan-title-mkt {{
            font-size: 14px;
            font-weight: 700;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .plan-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }}
        .plan-item {{
            background: rgba(0, 0, 0, 0.3);
            padding: 10px 12px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .plan-item .label {{ font-size: 11px; color: #9ca3af; margin-bottom: 2px; }}
        .plan-item .val {{ font-size: 17px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}

        /* Metrics Strip */
        .metrics-strip {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 12px;
        }}
        .metric-card {{
            background: #191d29;
            border: 1px solid #232734;
            border-radius: 8px;
            padding: 12px 14px;
        }}
        .metric-label {{ font-size: 11px; color: #8e918f; font-weight: 600; text-transform: uppercase; }}
        .metric-value {{ font-size: 20px; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 4px; }}
        .metric-sub {{ font-size: 11px; color: #c4c7c5; margin-top: 2px; }}

        /* GEX Level Matrix */
        .gex-matrix {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            background: #181c26;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #232734;
            margin-top: 14px;
        }}
        .gex-node {{
            border-left: 3px solid #0b57d0;
            padding-left: 10px;
        }}
        .gex-node.put {{ border-left-color: #c598ff; }}
        .gex-node.call {{ border-left-color: #06bbdf; }}
        .gex-node.zg {{ border-left-color: #ff5252; }}
        .gex-node.floor {{ border-left-color: #10b981; }}

        .wall-alert-box {{
            margin-top: 14px;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 13px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
            line-height: 1.5;
        }}
        .wall-alert-box.inverted {{
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid #f59e0b;
            color: #fbbf24;
        }}
        .wall-alert-box.solid {{
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid #10b981;
            color: #34d399;
        }}

        .bullet-list {{
            margin: 10px 0 0 0;
            padding-left: 20px;
            font-size: 13.5px;
            color: #d1d5db;
        }}
        .bullet-list li {{ margin-bottom: 6px; }}

        .table-responsive {{ overflow-x: auto; }}
        table.matrix-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
            text-align: left;
        }}
        table.matrix-table th, table.matrix-table td {{
            padding: 12px 14px;
            border-bottom: 1px solid #232734;
        }}
        table.matrix-table th {{ background: #161922; color: #8e918f; font-weight: 600; }}
        table.matrix-table tr:hover {{ background: #181c28; }}

        .btn-link {{
            color: #3b82f6;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 13px;
        }}
        .btn-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>

    <div class="nav-tabs">
        <div class="brand-title">🏛️ クオンツ・コモディティ戦略レーダー</div>
        <button class="tab-btn active" onclick="switchTab('HE')">🐷 豚肉 (HE)</button>
        <button class="tab-btn" onclick="switchTab('NG')">🔥 天然ガス (NG)</button>
        <button class="tab-btn" onclick="switchTab('SI')">🥈 シルバー (SI)</button>
        <button class="tab-btn" onclick="switchTab('ZC')">🌽 トウモロコシ (ZC)</button>
        <button class="tab-btn" onclick="switchTab('SUMMARY')">📋 4銘柄総合マトリクス</button>
        <div class="header-meta">Updated: {now_str} | Data: CFTC & GEX Live</div>
    </div>

    <div class="container">
"""

    for sym in symbols:
        data = frontend_data[sym]
        sig = data["signal"]
        gex_info = data["gex"]
        gex_summary = sig.get("gex_summary", {})
        trade_plans = sig.get("trade_plans", {})
        plan_rec = trade_plans.get("recommended_limit_plan")
        plan_mkt = trade_plans.get("market_plan")

        badge_bg = sig.get("badge_color", "#8e918f")
        action_text = sig.get("action_label", "監視中")

        # Plan cards HTML
        trade_plans_html = ""
        if plan_rec:
            trade_plans_html = f"""
            <div class="plans-container">
                <!-- Recommended Pullback Limit Plan -->
                <div class="plan-card-recommended">
                    <div class="plan-header">
                        <div class="plan-title-rec">{plan_rec['name']}</div>
                        <span class="badge" style="background:#10b981; color:#000;">{plan_rec['direction']}</span>
                    </div>
                    <div class="plan-grid">
                        <div class="plan-item">
                            <div class="label">引きつけ指値目安</div>
                            <div class="val" style="color: #34d399;">{plan_rec['entry_range']}</div>
                        </div>
                        <div class="plan-item">
                            <div class="label">タイト損切り (SL)</div>
                            <div class="val" style="color: #f87171;">{plan_rec['stop_loss']}</div>
                        </div>
                        <div class="plan-item">
                            <div class="label">利確目標 (TP: Call壁)</div>
                            <div class="val" style="color: #38bdf8;">{plan_rec['take_profit']}</div>
                        </div>
                        <div class="plan-item">
                            <div class="label">リスクリワード比 (RR)</div>
                            <div class="val" style="color: #f59e0b; font-size: 19px;">1 : {plan_rec['risk_reward_ratio']}</div>
                        </div>
                        <div class="plan-item">
                            <div class="label">リスク幅 / リワード幅</div>
                            <div class="val" style="font-size: 14px;">{plan_rec['risk_distance']} / {plan_rec['reward_distance']}</div>
                        </div>
                    </div>
                    <div style="font-size: 12.5px; color: #d1d5db; margin-top: 10px;">
                        💡 <strong>戦略設計メモ:</strong> {plan_rec['strategy_memo']}
                    </div>
                </div>

                <!-- Market Plan (Secondary) -->
                <div class="plan-card-market">
                    <div class="plan-header">
                        <div class="plan-title-mkt">{plan_mkt['name']}</div>
                        <span style="font-size: 12px; color: #94a3b8;">RR: 1 : {plan_mkt['risk_reward_ratio']}</span>
                    </div>
                    <div style="display: flex; gap: 20px; font-size: 13px; font-family: monospace; color: #cbd5e1;">
                        <span>エントリー: {plan_mkt['entry_target']}</span>
                        <span>SL: {plan_mkt['stop_loss']}</span>
                        <span>TP: {plan_mkt['take_profit']}</span>
                        <span style="color: #f59e0b;">(リスク幅: {plan_mkt['risk_distance']})</span>
                    </div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                        ⚠️ {plan_mkt['strategy_memo']}
                    </div>
                </div>
            </div>
            """

        signals_bullets_html = "".join([f"<li>{s}</li>" for s in sig.get("signals", [])])

        c_idx = sig["cot_summary"]["commercial_index"]
        m_idx = sig["cot_summary"]["managed_money_index"]
        c_net = sig["cot_summary"]["commercial_net"]
        m_net = sig["cot_summary"]["managed_money_net"]
        c_chg = sig["cot_summary"]["commercial_weekly_chg"]
        m_chg = sig["cot_summary"]["managed_money_weekly_chg"]
        cot_lag = sig["cot_summary"].get("cot_lag_note", "通常推移")

        # Inversion Alert Styling
        is_inverted = gex_summary.get("put_wall_inverted", False)
        wall_alert_class = "inverted" if is_inverted else "solid"

        active_class = "active" if sym == "HE" else ""

        html_content += f"""
        <!-- TAB: {sym} -->
        <div id="tab-{sym}" class="tab-pane {active_class}">
            
            <!-- Top Row: Overview, Dual Plans, GEX Matrix -->
            <div class="top-row-grid">
                <!-- Left: Signals & Dual Plans -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">
                            {sym_icons[sym]} {sig['name']}
                            <span style="font-size: 13px; color: #38bdf8; font-weight: 600;">[{sig.get('active_contract', '')}]</span>
                            <span style="font-size: 12px; color: #8e918f; font-weight: normal;">({sig['rakuten_name']})</span>
                        </div>
                        <span class="badge" style="background: {badge_bg}; color: #000;">{action_text}</span>
                    </div>

                    <div class="metrics-strip">
                        <div class="metric-card">
                            <div class="metric-label">現在値 (Spot)</div>
                            <div class="metric-value">{sig['spot_price']}</div>
                            <div class="metric-sub">{sig['unit']}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">商業筋 COT指数</div>
                            <div class="metric-value" style="color: {'#34d399' if c_idx >= 80 else '#fff'};">{c_idx}%</div>
                            <div class="metric-sub">{c_net:+,} 枚 (週変: {c_chg:+,})</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">ファンド COT指数</div>
                            <div class="metric-value" style="color: {'#f87171' if m_idx <= 20 else '#fff'};">{m_idx}%</div>
                            <div class="metric-sub">{m_net:+,} 枚 (週変: {m_chg:+,})</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">実質防衛床 (Floor)</div>
                            <div class="metric-value" style="font-size: 16px; color: #34d399;">
                                {gex_summary.get('floor_label', 'Put Wall')}
                            </div>
                            <div class="metric-sub">Zero-Gamma: {gex_info.get('zero_gamma')}</div>
                        </div>
                    </div>

                    <!-- Put Wall Inversion Alert -->
                    <div class="wall-alert-box {wall_alert_class}">
                        <div style="font-size: 18px;">{'⚠️' if is_inverted else '🛡️'}</div>
                        <div>{gex_summary.get('put_wall_status_desc', '')}</div>
                    </div>

                    {trade_plans_html}

                    <div style="margin-top: 16px;">
                        <div style="font-size: 14px; font-weight: 700; color: #e5e7eb;">📊 4層コンフルエンス根拠:</div>
                        <ul class="bullet-list">
                            {signals_bullets_html}
                        </ul>
                    </div>
                </div>

                <!-- Right: Options GEX Cross-Matrix & Calendar Spread Monitor -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">🛡️ GEX重力場 ＆ スプレッド監視</div>
                        <a href="{gex_info.get('url', '#')}" target="_blank" class="btn-link">GEXレーダー詳細 ↗</a>
                    </div>
                    <div class="gex-matrix">
                        <div class="gex-node put">
                            <div style="font-size: 11px; color: #c598ff; font-weight: bold;">Put Wall Strike</div>
                            <div style="font-size: 19px; font-weight: 700; font-family: monospace;">{gex_info.get('put_wall') or 'N/A'}</div>
                            <div style="font-size: 10px; color: #8e918f;">{'※割れ・抵抗反転中' if is_inverted else '機関支持線'}</div>
                        </div>
                        <div class="gex-node zg">
                            <div style="font-size: 11px; color: #ff5252; font-weight: bold;">Zero-Gamma (ZG)</div>
                            <div style="font-size: 19px; font-weight: 700; font-family: monospace;">{gex_info.get('zero_gamma') or 'N/A'}</div>
                            <div style="font-size: 10px; color: #8e918f;">レジーム境界ピボット</div>
                        </div>
                        <div class="gex-node call">
                            <div style="font-size: 11px; color: #06bbdf; font-weight: bold;">Call Wall Strike</div>
                            <div style="font-size: 19px; font-weight: 700; font-family: monospace;">{gex_info.get('call_wall') or 'N/A'}</div>
                            <div style="font-size: 10px; color: #8e918f;">利確目標の天井</div>
                        </div>
                    </div>

                    <!-- COT 3-Day Lag Heuristics Box -->
                    <div style="margin-top: 14px; background: #171b26; padding: 14px; border-radius: 8px; border-left: 4px solid #38bdf8;">
                        <div style="font-size: 13px; font-weight: bold; color: #38bdf8;">🕒 COT集計タイムラグ（火曜➔金曜）手口補正</div>
                        <div style="font-size: 12.5px; color: #cbd5e1; margin-top: 4px; line-height: 1.5;">{cot_lag}</div>
                    </div>

                    <!-- Calendar Spread Monitor Box -->
                    <div style="margin-top: 12px; background: #171b26; padding: 14px; border-radius: 8px; border-left: 4px solid #f9ab00;">
                        <div style="font-size: 13px; font-weight: bold; color: #f9ab00;">📅 限月 ＆ カレンダースプレッド動向</div>
                        <div style="font-size: 12.5px; color: #cbd5e1; margin-top: 4px; line-height: 1.5;">
                            <strong>期近/期先:</strong> {data['spread_monitor'].get('current_contract', '')} ➔ {data['spread_monitor'].get('next_contract', '')}<br>
                            <strong>サヤ力学:</strong> {data['spread_monitor'].get('spread_dynamics', '')}
                        </div>
                    </div>

                    <div style="margin-top: 12px; background: #171b26; padding: 12px; border-radius: 8px; font-size: 12.5px; color: #9ca3af;">
                        <div style="font-weight: bold; color: #e5e7eb; margin-bottom: 3px;">🤖 GEX AIインサイト要約:</div>
                        {gex_info.get('ai_summary', '')}
                    </div>
                </div>
            </div>

            <!-- Chart Panel 1: Price & COT Net Positions -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">📈 価格推移 ＆ 大口投機筋 vs 商業筋 ネットポジション（過去3年）</div>
                    <span style="font-size: 12px; color: #8e918f;">CFTC Disaggregated Futures & Options Weekly Data</span>
                </div>
                <div id="chart-cot-{sym}" style="height: 460px; width: 100%;"></div>
            </div>

            <!-- Chart Panel 2: 3-Year COT Index (Oscillator) & Net Weekly Change -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚡ 3年 COT Index（0〜100%過熱度オシレーター）＆ ネットポジション週次増減</div>
                    <span style="font-size: 12px; color: #8e918f;">Larry Williams Style Quant Metric</span>
                </div>
                <div id="chart-osc-{sym}" style="height: 360px; width: 100%;"></div>
            </div>

        </div>
        """

    # --- Render Summary Tab ---
    html_content += """
        <!-- TAB: SUMMARY -->
        <div id="tab-SUMMARY" class="tab-pane">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">📋 4大コモディティ 総合クオンツ・マトリクス比較</div>
                    <span style="font-size: 12px; color: #8e918f;">楽天CFD 対象銘柄</span>
                </div>
                <div class="table-responsive">
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th>銘柄 / 対象限月</th>
                                <th>Spot</th>
                                <th>総合シグナル</th>
                                <th>商業筋COT</th>
                                <th>ファンドCOT</th>
                                <th>GEXレジーム</th>
                                <th>実質防衛床 (Floor)</th>
                                <th>Call Wall (天井)</th>
                                <th>【推奨】引きつけ指値プラン (RR)</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    for sym in symbols:
        sig = signals_data[sym]
        gex_info = gex_data[sym]
        gex_summary = sig.get("gex_summary", {})
        plan_rec = sig.get("trade_plans", {}).get("recommended_limit_plan")
        c_idx = sig["cot_summary"]["commercial_index"]
        m_idx = sig["cot_summary"]["managed_money_index"]

        plan_desc = f"指値: {plan_rec['entry_range']} (SL: {plan_rec['stop_loss']} / TP: {plan_rec['take_profit']}) <span style='color:#f59e0b; font-weight:bold;'>[RR 1:{plan_rec['risk_reward_ratio']}]</span>" if plan_rec else "レンジ監視 / 条件待ち"

        html_content += f"""
                            <tr>
                                <td style="font-weight: 700;">
                                    {sym_icons[sym]} {sig['name']}<br>
                                    <span style="font-size: 11px; color: #38bdf8;">{sig.get('active_contract', '')}</span>
                                </td>
                                <td style="font-family: monospace; font-weight: bold;">{sig['spot_price']}</td>
                                <td><span class="badge" style="background:{sig['badge_color']}; color:#000;">{sig['action_label']}</span></td>
                                <td style="font-family: monospace; font-weight: bold; color: {'#34d399' if c_idx >= 80 else '#fff'};">{c_idx}%</td>
                                <td style="font-family: monospace; font-weight: bold; color: {'#f87171' if m_idx <= 20 else '#fff'};">{m_idx}%</td>
                                <td style="font-size: 12px;">{'🟢 Positive' if gex_info.get('is_positive_gamma') else '🔴 Negative'}</td>
                                <td style="font-family: monospace; color: #34d399; font-weight: bold;">{gex_summary.get('floor_label', '-')}</td>
                                <td style="font-family: monospace; color: #06bbdf; font-weight: bold;">{gex_info.get('call_wall') or '-'}</td>
                                <td style="font-size: 12.5px;">{plan_desc}</td>
                            </tr>
        """

    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Strategy Guide Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">📖 戦略運用ルール ＆ 実戦ピット迎撃手順</div>
                </div>
                <div style="font-size: 14px; line-height: 1.7; color: #d1d5db;">
                    <p><strong>■ プロ仕様の4層融合クオンツ設計:</strong></p>
                    <ol>
                        <li><strong>COTレポート（爆薬の充填度）:</strong> 商業筋COT指数 80%以上 ＆ ファンド指数 20%以下はショートスクイーズの爆薬満タン。さらに週半ばの日次出来高・取組高で投げ売り完了を確認。</li>
                        <li><strong>GEX壁の動的判定（物理的防衛線）:</strong> SpotがPut Wallを下回った場合は一時的なレジスタンス反転を警戒し、防衛床を「Zero-Gamma」へ自動スイッチ。</li>
                        <li><strong>引きつけ指値アルゴリズム（神リスクリワード）:</strong> 成行で飛びつかず、Zero-Gammaや防衛床への押し目をミリ単位で引きつける指値を投入。SLを直下にタイト配置することで【RR 1:3〜1:6】の損小利大を強制執行。</li>
                        <li><strong>限月＆カレンダースプレッド:</strong> 期近のディスカウントから期先への需要回復期スプレッドを監視し、ロールオーバー時のコスト負けを排除。</li>
                    </ol>
                </div>
            </div>
        </div>
    </div>

    <!-- Embed Data & Chart Initialization Scripts -->
    <script>
        const appData = """ + json.dumps(frontend_data, ensure_ascii=False) + """;

        function switchTab(sym) {
            document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            const targetPane = document.getElementById('tab-' + sym);
            if (targetPane) targetPane.classList.add('active');
            
            const btn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.textContent.includes(sym) || (sym === 'SUMMARY' && b.textContent.includes('マトリクス')));
            if (btn) btn.classList.add('active');

            window.dispatchEvent(new Event('resize'));
        }

        document.addEventListener('DOMContentLoaded', () => {
            const symbols = ['HE', 'NG', 'SI', 'ZC'];
            
            symbols.forEach(sym => {
                const item = appData[sym];
                if (!item) return;

                const cotRows = item.cot;
                const cotDates = cotRows.map(r => r.date);
                const commNet = cotRows.map(r => r.commercials.net);
                const mmNet = cotRows.map(r => r.managed_money.net);
                const commIdx = cotRows.map(r => r.cot_index.commercials);
                const mmIdx = cotRows.map(r => r.cot_index.managed_money);
                const commChg = cotRows.map(r => r.weekly_net_change.commercials);

                const priceRows = item.price;
                const pDates = priceRows.map(r => r.date);
                const pCloses = priceRows.map(r => r.close);

                // 1. Price + COT Net Position Chart
                const tracePrice = {
                    x: pDates,
                    y: pCloses,
                    name: '先物価格 (Spot/Close)',
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#ffffff', width: 2 },
                    yaxis: 'y2'
                };
                const traceCommNet = {
                    x: cotDates,
                    y: commNet,
                    name: '商業筋 (Commercials) ネット枚数',
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#38bdf8', width: 2.5 },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(56, 189, 248, 0.12)'
                };
                const traceMMNet = {
                    x: cotDates,
                    y: mmNet,
                    name: '投機筋 (Managed Money) ネット枚数',
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#fb923c', width: 2, dash: 'dot' }
                };

                const layoutCot = {
                    paper_bgcolor: '#141721',
                    plot_bgcolor: '#141721',
                    margin: { l: 60, r: 60, t: 30, b: 40 },
                    legend: { orientation: 'h', y: 1.12, font: { color: '#c4c7c5' } },
                    xaxis: { gridcolor: '#232734', color: '#8e918f' },
                    yaxis: {
                        title: 'COT Net Position (枚)',
                        gridcolor: '#232734',
                        color: '#38bdf8',
                        zerolinecolor: '#475569'
                    },
                    yaxis2: {
                        title: '価格 (' + item.unit + ')',
                        overlaying: 'y',
                        side: 'right',
                        color: '#ffffff',
                        showgrid: false
                    }
                };
                Plotly.newPlot('chart-cot-' + sym, [traceCommNet, traceMMNet, tracePrice], layoutCot, { responsive: true, displayModeBar: false });

                // 2. COT Index Oscillator & Weekly Change Chart
                const traceCommIdx = {
                    x: cotDates,
                    y: commIdx,
                    name: '商業筋 COT Index (%)',
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#34d399', width: 2 }
                };
                const traceMMIdx = {
                    x: cotDates,
                    y: mmIdx,
                    name: 'ファンド COT Index (%)',
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#f87171', width: 2, dash: 'dash' }
                };
                const traceCommChg = {
                    x: cotDates,
                    y: commChg,
                    name: '商業筋 週次増減',
                    type: 'bar',
                    marker: { color: commChg.map(v => v >= 0 ? 'rgba(52, 211, 153, 0.4)' : 'rgba(248, 113, 113, 0.4)') },
                    yaxis: 'y2'
                };

                const layoutOsc = {
                    paper_bgcolor: '#141721',
                    plot_bgcolor: '#141721',
                    margin: { l: 60, r: 60, t: 30, b: 40 },
                    legend: { orientation: 'h', y: 1.14, font: { color: '#c4c7c5' } },
                    xaxis: { gridcolor: '#232734', color: '#8e918f' },
                    yaxis: {
                        title: 'COT Index (%)',
                        range: [0, 100],
                        gridcolor: '#232734',
                        color: '#c4c7c5'
                    },
                    yaxis2: {
                        title: '週次変化 (枚)',
                        overlaying: 'y',
                        side: 'right',
                        color: '#8e918f',
                        showgrid: false
                    },
                    shapes: [
                        { type: 'line', y0: 80, y1: 80, x0: cotDates[0], x1: cotDates[cotDates.length - 1], line: { color: '#34d399', width: 1.5, dash: 'dot' } },
                        { type: 'line', y0: 20, y1: 20, x0: cotDates[0], x1: cotDates[cotDates.length - 1], line: { color: '#f87171', width: 1.5, dash: 'dot' } }
                    ]
                };
                Plotly.newPlot('chart-osc-' + sym, [traceCommIdx, traceMMIdx, traceCommChg], layoutOsc, { responsive: true, displayModeBar: false });
            });
        });
    </script>
</body>
</html>
"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    index_file = os.path.join(DOCS_DIR, "index.html")
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[Success] Upgraded dashboard generated at {index_file}")
    return index_file


if __name__ == "__main__":
    generate_dashboard()
