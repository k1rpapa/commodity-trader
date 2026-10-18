"""
Main Orchestrator for Commodity Trader
Runs the end-to-end quant pipeline:
1. COT Data Fetcher (CFTC Disaggregated reports)
2. GEX Data Fetcher (options-gex-radar)
3. Price & Technical Fetcher (Yahoo Finance)
4. 4-Layer Signal Engine (COT x Seasonality x GEX x ATR)
5. Interactive Dashboard Generator (docs/index.html)
6. LINE Trade Alert Notifier
"""

import sys
import argparse
from src.data.cot_fetcher import update_and_calculate_indices
from src.data.gex_fetcher import fetch_gex_data
from src.data.price_fetcher import fetch_and_calculate_prices
from src.analysis.signal_engine import generate_all_signals
from src.generator.dashboard_generator import generate_dashboard
from src.alerts.line_notifier import send_line_alert


def run_pipeline(send_notification: bool = True, dry_run: bool = False, refresh_history: bool = False):
    print("=" * 60)
    print("🚀 クオンツ・コモディティ戦略パイプライン 実行開始")
    print("=" * 60)

    # 1. Fetch COT Data
    print("\n[Step 1/5] CFTC COTデータ取得 & 3年COT Index計算...")
    update_and_calculate_indices(force_refresh_history=refresh_history)

    # 2. Fetch GEX Data
    print("\n[Step 2/5] オプションGEXデータ取得 (options-gex-radar)...")
    fetch_gex_data()

    # 3. Fetch Price Data
    print("\n[Step 3/5] 先物価格・テクニカル指標取得 (Yahoo Finance)...")
    fetch_and_calculate_prices()

    # 4. Generate Trade Signals
    print("\n[Step 4/5] 4層クオンツ統合シグナル判定...")
    signals = generate_all_signals()

    # 5. Build Dashboard
    print("\n[Step 5/5] 静的HTMLダッシュボード生成 (docs/index.html)...")
    generate_dashboard()

    # 6. Send LINE Notification
    if send_notification:
        print("\n[LINE通知] トレード指示メッセージ生成・送信...")
        send_line_alert(dry_run=dry_run)

    print("\n" + "=" * 60)
    print("🎉 パイプライン全工程が正常に完了しました！")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Commodity Trader Pipeline Runner")
    parser.add_argument("--dry-run", action="store_true", help="Print LINE message without sending")
    parser.add_argument("--no-notify", action="store_true", help="Skip sending LINE notifications")
    parser.add_argument("--refresh-history", action="store_true", help="Force re-download 3-year COT history")
    args = parser.parse_args()

    run_pipeline(
        send_notification=not args.no_notify,
        dry_run=args.dry_run,
        refresh_history=args.refresh_history
    )
