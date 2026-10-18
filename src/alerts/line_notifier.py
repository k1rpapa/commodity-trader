"""
LINE Notifier (Institutional Upgrade)
Sends structured, actionable trading signals and COT/GEX confluence alerts to LINE Messaging API.
Emphasizes the Recommended Pullback Limit Plan (high RR) and Put Wall inversion alerts.
"""

import os
import json
import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
SIGNALS_PATH = os.path.join(DATA_DIR, "signals_latest.json")

# GitHub Pages URL for the dashboard
DASHBOARD_URL = "https://k1rpapa.github.io/commodity-trader/"


def format_line_message(signals_data: dict) -> str:
    """Format signals into a readable, actionable LINE push message."""
    active_plans = []
    monitored = []

    for sym, d in signals_data.items():
        if d.get("trade_plans", {}).get("recommended_limit_plan"):
            active_plans.append(d)
        else:
            monitored.append(d)

    lines = []
    lines.append("🔔【クオンツ・コモディティ戦略: トレード指示】")
    lines.append("━━━━━━━━━━━━━━━━━━━━")

    if not active_plans:
        lines.append("本日は新規エントリー条件を満たす銘柄はありません。")
        lines.append("全銘柄ともに監視・引き付けフェーズです。")
    else:
        for p in active_plans:
            tp_rec = p["trade_plans"]["recommended_limit_plan"]
            cot = p["cot_summary"]
            gex = p["gex_summary"]
            contract = p.get("active_contract", "")
            
            lines.append(f"■ {p['name']} [{contract}]")
            lines.append(f"・判定: {p['action_label']}")
            lines.append(f"・売買: {tp_rec['direction']}")
            lines.append(f"・🌟【推奨】指値目安: {tp_rec['entry_range']} ({p['unit']})")
            lines.append(f"・タイト損切り (SL): {tp_rec['stop_loss']} ({gex.get('floor_label', '防衛線')}直下)")
            lines.append(f"・利確目標 (TP): {tp_rec['take_profit']} (Call壁手前)")
            lines.append(f"・リスクリワード: 1 : {tp_rec['risk_reward_ratio']} (神RR仕様)")
            if gex.get("put_wall_inverted"):
                lines.append(f"・⚠️ 注意: Put Wall割れ中。実質防衛床は{gex.get('floor_label')}")
            lines.append(f"・【根拠】COT商業筋: {cot['commercial_index']}% / ファンド: {cot['managed_money_index']}%")
            lines.append("────────────────────")

    if monitored:
        lines.append("【監視継続】")
        for m in monitored:
            contract = m.get("active_contract", "")
            lines.append(f"・{m['name']} [{contract}]: {m['action_label']} (Spot: {m['spot_price']})")
        lines.append("━━━━━━━━━━━━━━━━━━━━")

    lines.append(f"📊 詳細チャート・COT＆GEXダッシュボード:")
    lines.append(DASHBOARD_URL)
    lines.append("※成行ではなく「引きつけ指値」で注文を装填してください。")

    return "\n".join(lines)


def send_line_alert(dry_run: bool = False):
    """Send LINE message using LINE Messaging API."""
    if not os.path.exists(SIGNALS_PATH):
        print("[Error] Signals file not found.")
        return

    with open(SIGNALS_PATH, "r", encoding="utf-8") as f:
        signals_data = json.load(f)

    msg_text = format_line_message(signals_data)

    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    if dry_run or not token or not user_id:
        print("\n=== [LINE通知 プレビュー (Dry-Run)] ===")
        print(msg_text)
        print("=========================================\n")
        if not token or not user_id:
            print("[Info] LINE_CHANNEL_ACCESS_TOKEN または LINE_USER_ID が未設定のため、プレビュー表示しました。")
            print("       本番送信する場合は環境変数または .env に設定してください。")
        return msg_text

    # Send via LINE Messaging API
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "messages": [
            {
                "type": "text",
                "text": msg_text
            }
        ]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            print("[Success] LINE alert sent successfully!")
        else:
            print(f"[Error] Failed to send LINE alert: HTTP {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[Error] Exception sending LINE message: {e}")


if __name__ == "__main__":
    send_line_alert(dry_run=True)
