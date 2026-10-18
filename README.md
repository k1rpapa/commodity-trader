# 🏛️ クオンツ・コモディティ戦略レーダー ＆ CFDトレード指示システム

コモディティ先物（銀・天然ガス・コーン・豚肉）の **COTレポート（大口需給） × 季節性サイクル × オプションGEX（防衛壁） × ATR資金管理** を統合し、高確度なトレード指示の生成とインタラクティブ・ダッシュボードの公開を全自動で行うシステムです。

---

## 🎯 対象4大コモディティ（楽天CFD対応）

| 銘柄 | 取引所 | 楽天CFD名称 | 特徴 ＆ 戦略アプローチ |
| :--- | :--- | :--- | :--- |
| 🐷 **豚肉先物 (HE)** | CME | 豚肉先物CFD | 感謝祭・年末ハム需要に向けた秋の底打ちアノマリー ＆ 記録的ショートスクイーズ |
| 🔥 **天然ガス先物 (NG)** | NYMEX | 天然ガスCFD | 冬期暖房需要プレミアム ＆ 在庫急減による急騰初動狙い |
| 🥈 **銀先物 (SI)** | CME | シルバーCFD | 貴金属年末ラリーアノマリー ＆ Put GEX防衛線を背にした押し目買い |
| 🌽 **トウモロコシ先物 (ZC)** | CBOT | コーンCFD | 収穫圧力（Harvest Pressure）の一巡・自律反発ゾーン監視 |

---

## 🧠 4層統合クオンツ・フレームワーク

```
【第1層: COTレポート（爆薬の充填度）】
   ・米CFTCから毎週最新データを自動取得。
   ・過去3年の「商業筋（実需・スマートマネー）」と「投機筋（ヘッジファンド）」の手口から
     COT Index（0〜100%）を算出。ファンドの売り極限 ＆ 実需の買い集めを検知。
   ↓
【第2層: 季節性サイクル（風向き）】
   ・過去の価格アノマリーと照合し、歴史的に「買いが有利な時期」のみにエントリーを厳選。
   ↓
【第3層: オプションGEXレーダー（物理的な防衛壁）】
   ・既存の options-gex-radar から Put Wall（支持線）・Call Wall（抵抗線）・Zero-Gammaを連動。
   ・損切り（SL）は機関投資家の買い支えがある Put Wall 直下に配置し、無駄な狩られ損を防止。
   ・利確目標（TP）は Call Wall 手前に配置して確実に利益をロック。
   ↓
【第4層: テクニカル ＆ ATR資金管理（発射台と安全装置）】
   ・日足20/50 EMA、RSI(14)、ATR(14) に基づく動的サイジング。
   ・1トレードあたりの許容損失を口座資金の 1.0%〜2.0% に厳格管理。
```

---

## 📁 ディレクトリ構成

```text
commodity-trader/
├── .github/workflows/
│   └── weekly_update.yml       # 毎週土曜朝にデータ更新・ビルド・LINE配信を全自動実行
├── src/
│   ├── data/
│   │   ├── cot_fetcher.py      # CFTCからCOTデータ取得 & 3年COT Index計算
│   │   ├── gex_fetcher.py      # options-gex-radar から壁・レジーム抽出
│   │   └── price_fetcher.py    # Yahoo FinanceからOHLCV & テクニカル計算
│   ├── analysis/
│   │   └── signal_engine.py    # 4層統合スコアリング ＆ トレード計画立案
│   ├── generator/
│   │   └── dashboard_generator.py # Plotlyを用いたHTMLダッシュボード（docs/）生成
│   └── alerts/
│       └── line_notifier.py    # LINE Messaging APIへのトレード指示配信
├── data/                       # 取得データキャッシュ（cot_history, gex, prices）
├── docs/                       # GitHub Pages公開ディレクトリ（index.html）
├── main.py                     # 全パイプライン統括実行スクリプト
└── requirements.txt
```

---

## 🚀 使い方

### 1. ローカルでの実行
```bash
# 依存ライブラリのインストール
pip install -r requirements.txt

# パイプライン全実行（データ取得 ➔ シグナル判定 ➔ HTML生成 ➔ LINE通知プレビュー）
python main.py --dry-run
```

生成されたダッシュボードは `docs/index.html` をブラウザで直接開いて確認できます。

### 2. GitHub Pages の設定
1. このリポジトリを GitHub にプッシュします。
2. GitHubリポジトリの **Settings ➔ Pages** を開きます。
3. **Branch** を `main`、フォルダを `/docs` に設定して保存します。
4. 数分後、`https://<ユーザー名>.github.io/commodity-trader/` にダッシュボードが公開されます。

### 3. LINE通知の設定（完全自動化）
LINE Official Account（Messaging API）のトークンを取得し、GitHub リポジトリの **Settings ➔ Secrets and variables ➔ Actions** に登録します。

* `LINE_CHANNEL_ACCESS_TOKEN`: チャネルアクセストークン（長期）
* `LINE_USER_ID`: あなたのLINEユーザーID

毎週土曜日午前（CFTCレポート公開直後）に GitHub Actions が自動起動し、ダッシュボードが更新され、スマートフォンにトレード指示がプッシュ通知されます。
