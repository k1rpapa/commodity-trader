"""
Dashboard Generator
Generates an interactive, responsive HTML dashboard in docs/ for GitHub Pages.
Features Dark Mode, Plotly.js charts, COT Net Position + Index, GEX Walls, and Rakuten CFD Trade Plans.
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

    # Order of tabs: HE, NG, SI, ZC, SUMMARY
    symbols = ["HE", "NG", "SI", "ZC"]
    sym_icons = {"HE": "🐷", "NG": "🔥", "SI": "🥈", "ZC": "🌽"}

    # Prepare datasets for frontend embed
    frontend_data = {}
    for sym in symbols:
        c_rows = cot_data.get(sym, [])
        p_hist = price_data.get(sym, {}).get("history", [])
        sig = signals_data.get(sym, {})
        gex_info = gex_data.get(sym, {})

        # Downsample price if too large (keep weekly or daily last 3 years)
        # c_rows are weekly dates
        frontend_data[sym] = {
            "name": sig.get("name", sym),
            "rakuten_name": sig.get("rakuten_name", ""),
            "unit": sig.get("unit", ""),
            "signal": sig,
            "gex": gex_info,
            "cot": c_rows,
            "price": p_hist[-300:] if len(p_hist) > 300 else p_hist # Last ~300 trading days
        }

    html_content = f"""<!DOCTYPE html>
<html lang="ja" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quant Commodity Radar & CFD Trader (COT × 季節性 × GEX)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            background-color: #101218;
            color: #ffffff;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.5;
        }}
        .nav-tabs {{
            background: #161922;
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
            background: #1f2330;
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
        .tab-btn.active {{ background: #0b57d0; color: #fff; border-color: #3b82f6; }}
        .header-meta {{
            margin-left: auto;
            font-size: 12px;
            color: #8e918f;
            font-family: 'JetBrains Mono', monospace;
        }}
        .container {{
            max-width: 1650px;
            margin: 0 auto;
            padding: 24px 20px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}
        .tab-pane {{ display: none; }}
        .tab-pane.active {{ display: flex; flex-direction: column; gap: 24px; }}
        
        /* Grid Layout */
        .top-row-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }}
        @media (min-width: 1024px) {{
            .top-row-grid {{ grid-template-columns: 1.15fr 0.85fr; }}
        }}

        .card {{
            background: #141720;
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
        
        /* Trade Plan Box */
        .trade-plan-box {{
            background: rgba(11, 87, 208, 0.1);
            border: 1px solid #0b57d0;
            border-radius: 10px;
            padding: 18px;
            margin-top: 12px;
        }}
        .plan-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }}
        .plan-item {{
            background: #1a1e2b;
            padding: 10px 14px;
            border-radius: 6px;
            border: 1px solid #282f42;
        }}
        .plan-item .label {{ font-size: 12px; color: #8e918f; margin-bottom: 4px; }}
        .plan-item .val {{ font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}

        /* Metrics Strip */
        .metrics-strip {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
        }}
        .metric-card {{
            background: #181c26;
            border: 1px solid #232734;
            border-radius: 8px;
            padding: 14px 16px;
        }}
        .metric-label {{ font-size: 12px; color: #8e918f; font-weight: 600; text-transform: uppercase; }}
        .metric-value {{ font-size: 22px; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 4px; }}
        .metric-sub {{ font-size: 12px; color: #c4c7c5; margin-top: 2px; }}

        /* GEX Level Matrix */
        .gex-matrix {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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

        .bullet-list {{
            margin: 10px 0 0 0;
            padding-left: 20px;
            font-size: 14px;
            color: #d1d5db;
        }}
        .bullet-list li {{ margin-bottom: 6px; }}

        /* Summary Table */
        .table-responsive {{ overflow-x: auto; }}
        table.matrix-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            text-align: left;
        }}
        table.matrix-table th, table.matrix-table td {{
            padding: 14px 16px;
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

    # --- Render Individual Tabs for each Commodity ---
    for sym in symbols:
        data = frontend_data[sym]
        sig = data["signal"]
        gex_info = data["gex"]
        tp = sig.get("trade_plan")

        badge_bg = sig.get("badge_color", "#8e918f")
        action_text = sig.get("action_label", "監視中")

        trade_plan_html = ""
        if tp:
            trade_plan_html = f"""
            <div class="trade-plan-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 700; font-size: 16px; color: #60a5fa;">🎯 楽天CFD 実践トレード指示プラン</div>
                    <span class="badge" style="background:#0b57d0; color:#fff;">{tp['direction']}</span>
                </div>
                <div class="plan-grid">
                    <div class="plan-item">
                        <div class="label">エントリー目安</div>
                        <div class="val" style="color: #60a5fa;">{tp['entry_price']}</div>
                    </div>
                    <div class="plan-item">
                        <div class="label">損切り (SL: 防衛壁下)</div>
                        <div class="val" style="color: #f87171;">{tp['stop_loss']}</div>
                    </div>
                    <div class="plan-item">
                        <div class="label">利確目標 (TP: 抵抗手前)</div>
                        <div class="val" style="color: #34d399;">{tp['take_profit']}</div>
                    </div>
                    <div class="plan-item">
                        <div class="label">リスクリワード比 (RR)</div>
                        <div class="val" style="color: #fbbf24;">1 : {tp['risk_reward_ratio']}</div>
                    </div>
                    <div class="plan-item">
                        <div class="label">日足 ATR (14)</div>
                        <div class="val">{tp['atr_14']}</div>
                    </div>
                </div>
                <div style="font-size: 13px; color: #c4c7c5; margin-top: 10px;">
                    💡 <strong>執行メモ:</strong> {tp['notes']}
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

        active_class = "active" if sym == "HE" else ""

        html_content += f"""
        <!-- TAB: {sym} -->
        <div id="tab-{sym}" class="tab-pane {active_class}">
            
            <!-- Top Row: Overview & Trade Plan -->
            <div class="top-row-grid">
                <!-- Left: Signals & Analysis -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">
                            {sym_icons[sym]} {sig['name']}
                            <span style="font-size: 13px; color: #8e918f; font-weight: normal;">({sig['rakuten_name']})</span>
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
                            <div class="metric-label">GEX レジーム</div>
                            <div class="metric-value" style="font-size: 15px; color: {'#34d399' if gex_info.get('is_positive_gamma') else '#f87171'};">
                                {'Positive Gamma' if gex_info.get('is_positive_gamma') else 'Negative Gamma'}
                            </div>
                            <div class="metric-sub">Zero-Gamma: {gex_info.get('zero_gamma')}</div>
                        </div>
                    </div>

                    {trade_plan_html}

                    <div style="margin-top: 18px;">
                        <div style="font-size: 14px; font-weight: 700; color: #e5e7eb;">📊 4層定性・定量コンフルエンス根拠:</div>
                        <ul class="bullet-list">
                            {signals_bullets_html}
                        </ul>
                    </div>
                </div>

                <!-- Right: Options GEX Cross-Matrix -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">🛡️ GEXオプション重力場 ＆ 防衛壁</div>
                        <a href="{gex_info.get('url', '#')}" target="_blank" class="btn-link">GEXレーダー詳細 ↗</a>
                    </div>
                    <div class="gex-matrix">
                        <div class="gex-node put">
                            <div style="font-size: 12px; color: #c598ff; font-weight: bold;">Put Wall (機関支持線)</div>
                            <div style="font-size: 20px; font-weight: 700; font-family: monospace;">{gex_info.get('put_wall') or 'N/A'}</div>
                            <div style="font-size: 11px; color: #8e918f;">損切りの安全な背</div>
                        </div>
                        <div class="gex-node zg">
                            <div style="font-size: 12px; color: #ff5252; font-weight: bold;">Zero-Gamma (転換線)</div>
                            <div style="font-size: 20px; font-weight: 700; font-family: monospace;">{gex_info.get('zero_gamma') or 'N/A'}</div>
                            <div style="font-size: 11px; color: #8e918f;">レジーム境界ピボット</div>
                        </div>
                        <div class="gex-node call">
                            <div style="font-size: 12px; color: #06bbdf; font-weight: bold;">Call Wall (機関抵抗線)</div>
                            <div style="font-size: 20px; font-weight: 700; font-family: monospace;">{gex_info.get('call_wall') or 'N/A'}</div>
                            <div style="font-size: 11px; color: #8e918f;">利確目標の天井</div>
                        </div>
                    </div>

                    <div style="margin-top: 16px; background: #161922; padding: 14px; border-radius: 8px; border-left: 4px solid #f9ab00;">
                        <div style="font-size: 13px; font-weight: bold; color: #f9ab00;">💡 GEXレーダー速報アラート</div>
                        <div style="font-size: 13px; color: #d1d5db; margin-top: 4px;">{gex_info.get('alert_text') or '安定推移中'}</div>
                    </div>

                    <div style="margin-top: 14px; background: #161922; padding: 14px; border-radius: 8px; font-size: 13px; color: #9ca3af;">
                        <div style="font-weight: bold; color: #e5e7eb; margin-bottom: 4px;">🤖 GEX AIインサイト抜粋:</div>
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
                <div id="chart-cot-{sym}" style="height: 480px; width: 100%;"></div>
            </div>

            <!-- Chart Panel 2: 3-Year COT Index (Oscillator) & Net Weekly Change -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚡ 3年 COT Index（0〜100%過熱度オシレーター）＆ ネットポジション週次増減</div>
                    <span style="font-size: 12px; color: #8e918f;">Larry Williams Style Quant Metric</span>
                </div>
                <div id="chart-osc-{sym}" style="height: 380px; width: 100%;"></div>
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
                                <th>銘柄</th>
                                <th>現在値 (Spot)</th>
                                <th>総合シグナル判定</th>
                                <th>商業筋COT指数</th>
                                <th>ファンドCOT指数</th>
                                <th>GEXレジーム</th>
                                <th>Put Wall (防衛線)</th>
                                <th>Call Wall (利確線)</th>
                                <th>トレード方針</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    for sym in symbols:
        sig = signals_data[sym]
        gex_info = gex_data[sym]
        tp = sig.get("trade_plan")
        tp_desc = f"{tp['direction']} (SL: {tp['stop_loss']} / TP: {tp['take_profit']})" if tp else "レンジ監視 / 静観"
        c_idx = sig["cot_summary"]["commercial_index"]
        m_idx = sig["cot_summary"]["managed_money_index"]

        html_content += f"""
                            <tr>
                                <td style="font-weight: 700;">{sym_icons[sym]} {sig['name']}</td>
                                <td style="font-family: monospace; font-weight: bold;">{sig['spot_price']}</td>
                                <td><span class="badge" style="background:{sig['badge_color']}; color:#000;">{sig['action_label']}</span></td>
                                <td style="font-family: monospace; font-weight: bold; color: {'#34d399' if c_idx >= 80 else '#fff'};">{c_idx}%</td>
                                <td style="font-family: monospace; font-weight: bold; color: {'#f87171' if m_idx <= 20 else '#fff'};">{m_idx}%</td>
                                <td style="font-size: 13px;">{'🟢 Positive' if gex_info.get('is_positive_gamma') else '🔴 Negative'}</td>
                                <td style="font-family: monospace; color: #c598ff;">{gex_info.get('put_wall') or '-'}</td>
                                <td style="font-family: monospace; color: #06bbdf;">{gex_info.get('call_wall') or '-'}</td>
                                <td style="font-size: 13px; color: #60a5fa;">{tp_desc}</td>
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
                    <div class="card-title">📖 戦略運用ルール ＆ 楽天CFDでの発注手順</div>
                </div>
                <div style="font-size: 14px; line-height: 1.7; color: #d1d5db;">
                    <p><strong>■ 4層融合戦略の基本思想:</strong></p>
                    <ol>
                        <li><strong>COTレポート（爆薬の充填度）:</strong> 商業筋COT指数が80%以上、ファンド指数が20%以下の局面は「ショートスクイーズ（踏み上げ急騰）」のエネルギーが極限まで溜まった状態です。</li>
                        <li><strong>季節性（風向き）:</strong> アノマリーが買い有利な月のみロングを検討し、特異年や逆風期での無謀なエントリーを遮断します。</li>
                        <li><strong>GEX壁（機関の防衛線）:</strong> 損切り（SL）は「Put Wall」の少し下に、利確目標（TP）は「Call Wall」の手前に配置し、機関投資家の実弾ヘッジを盾にします。</li>
                        <li><strong>資金管理（ATR）:</strong> 口座資金の1.0%〜2.0%以上の損失を出さないよう、損切り幅から逆算して楽天CFDの発注ロット数を決定します。</li>
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

            // Trigger window resize to ensure plotly renders correctly
            window.dispatchEvent(new Event('resize'));
        }

        // Render Plotly Charts for all symbols
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

                // Price history
                const priceRows = item.price;
                const pDates = priceRows.map(r => r.date);
                const pCloses = priceRows.map(r => r.close);
                const pSeasonal = priceRows.map(r => r.seasonal_avg);

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
                    paper_bgcolor: '#141720',
                    plot_bgcolor: '#141720',
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
                    paper_bgcolor: '#141720',
                    plot_bgcolor: '#141720',
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

    print(f"[Success] Interactive dashboard built at {index_file}")
    return index_file


if __name__ == "__main__":
    generate_dashboard()
