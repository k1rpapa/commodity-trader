"""
Larry Williams 2026 Forecast Quantitative Engine
Incorporates:
1. 2026 Mathematical Cycle Wave Roadmaps for all 19 Assets (Charts 4 to 109)
2. Day of Week Advantage (TDOW - Best trading days of the week)
3. Trading Day of Month Patterns (TDOM - Monthly anomalies)
4. Narita Calendar Days (TDOY exact converted calendar dates)
"""

from datetime import datetime, date, timezone, timedelta

# --- 1. 2026年 数理サイクル波形マスターデータ (全19銘柄) ---
LARRY_2026_CYCLES = {
    "ES": {
        "asset": "S&P 500 (ES)",
        "chart": "チャート4 (p.8)",
        "theme": "4年周期ボトム年。初春調整から6月16日大底、夏以降年末へ90%勝率の巨大上昇波",
        "monthly_phase": {
            1: {"phase": "PEAK_TO_CORRECTION", "direction": "DOWN", "bias": "年始高値警戒から調整入り", "score": -0.5},
            2: {"phase": "CORRECTION", "direction": "DOWN", "bias": "2月中旬から本格下落波動入り（70%の確率で下落）", "score": -1.0},
            3: {"phase": "PULLBACK", "direction": "DOWN", "bias": "下落トレンド継続・安値模索", "score": -1.0},
            4: {"phase": "PULLBACK", "direction": "DOWN", "bias": "中間反発を挟む底入れ前段", "score": -0.5},
            5: {"phase": "BOTTOMING", "direction": "BOTTOM", "bias": "5月下旬からベース形成・買い場接近", "score": 1.0},
            6: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【6月16日前後】2026年最大の買い場（大底完成）", "score": 2.0},
            7: {"phase": "RALLY_INITIAL", "direction": "UP", "bias": "夏の上昇ラリー初動", "score": 1.5},
            8: {"phase": "RALLY_ACCELERATION", "direction": "UP", "bias": "【90%の確率で上昇】年末へ向けた最強の上昇波スタート", "score": 2.0},
            9: {"phase": "RALLY", "direction": "UP", "bias": "秋のモメンタム加速期", "score": 1.5},
            10: {"phase": "RALLY_PULLBACK_BUY", "direction": "UP", "bias": "10月押し目完了から年末ラリー最終加速", "score": 1.5},
            11: {"phase": "RALLY_SURGE", "direction": "UP", "bias": "年間最高勝率の上昇トレンド継続", "score": 2.0},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "サンタクロースラリー・2027年高値トライ", "score": 1.5}
        },
        "tdow_bias": {0: "月曜買い（勝率81%最強バイアス）", 1: "火曜買い（週初買い優位）", 2: "中立", 3: "中立", 4: "利益確定"},
        "tdom_best": [1, 10, 11, 15]
    },
    "NQ": {
        "asset": "NASDAQ 100 (NQ)",
        "chart": "チャート4 (p.8 米国株連動)",
        "theme": "米株サイクル連動。春季調整から初夏大底、ハイテク主導の年末90%上昇波",
        "monthly_phase": {
            1: {"phase": "CORRECTION", "direction": "DOWN", "bias": "決算前の調整警戒", "score": -0.5},
            2: {"phase": "CORRECTION", "direction": "DOWN", "bias": "2月中旬以降のハイテク売り警戒", "score": -1.0},
            3: {"phase": "PULLBACK", "direction": "DOWN", "bias": "金利動向睨みの調整底模索", "score": -1.0},
            4: {"phase": "PULLBACK", "direction": "DOWN", "bias": "春の保ち合い", "score": -0.5},
            5: {"phase": "BOTTOMING", "direction": "BOTTOM", "bias": "大底形成ゾーン接近", "score": 1.0},
            6: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "初夏の大底完了・反転上昇開始", "score": 2.0},
            7: {"phase": "RALLY_INITIAL", "direction": "UP", "bias": "サマーラリー立ち上がり", "score": 1.5},
            8: {"phase": "RALLY_ACCELERATION", "direction": "UP", "bias": "年末ハイテクモメンタム波点火（90%上昇波）", "score": 2.0},
            9: {"phase": "RALLY", "direction": "UP", "bias": "新製品・AI投資加速波", "score": 1.5},
            10: {"phase": "RALLY", "direction": "UP", "bias": "秋の押し目完了から決算ラリー", "score": 1.5},
            11: {"phase": "RALLY_SURGE", "direction": "UP", "bias": "ブラックフライデー・年末強気波", "score": 2.0},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "年末高値圏到達", "score": 1.5}
        },
        "tdow_bias": {0: "月曜買い（週初買いバイアス）", 1: "火曜買い", 2: "中立", 3: "中立", 4: "利益確定"},
        "tdom_best": [1, 10, 11, 15]
    },
    "GC": {
        "asset": "ゴールド (GC)",
        "chart": "チャート84 (p.76)",
        "theme": "4月大底から【+72%青色上昇波】初夏急騰、8月中旬押しを経て年末高値トライ",
        "monthly_phase": {
            1: {"phase": "RALLY", "direction": "UP", "bias": "年始の現物買い需要", "score": 1.0},
            2: {"phase": "PULLBACK", "direction": "DOWN", "bias": "春先にかけての押し目形成期", "score": -0.5},
            3: {"phase": "PULLBACK", "direction": "DOWN", "bias": "大底に向けた最終ふるい落とし", "score": -0.5},
            4: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【4月年中最深ボトム】72%の確率で+72%上昇波スタート", "score": 2.0},
            5: {"phase": "RALLY_ACCELERATION", "direction": "UP", "bias": "【+72%青色上昇波】垂直上昇加速ゾーン", "score": 2.0},
            6: {"phase": "RALLY_PEAK", "direction": "TOP", "bias": "初夏の上昇波ターゲット到達・利益確定", "score": 1.0},
            7: {"phase": "CORRECTION", "direction": "DOWN", "bias": "夏枯れ調整期入り", "score": -0.5},
            8: {"phase": "SUMMER_BOTTOM", "direction": "BOTTOM", "bias": "8月中旬押し目完了・秋の買い場", "score": 1.5},
            9: {"phase": "RALLY", "direction": "UP", "bias": "秋の婚礼・中銀実需買い再点火", "score": 1.5},
            10: {"phase": "PULLBACK_BUY", "direction": "UP", "bias": "保ち合いから年末高値トライへ", "score": 1.0},
            11: {"phase": "RALLY", "direction": "UP", "bias": "年末現物需要立ち上がり", "score": 1.5},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "年間高値圏到達", "score": 1.5}
        },
        "tdow_bias": {0: "中立", 1: "中立", 2: "押し目形成", 3: "木曜買い（買いバイアス立ち上がり）", 4: "金曜買い（週末買いバイアス最強・最良日）"},
        "tdom_best": [1, 6]
    },
    "SI": {
        "asset": "シルバー (SI)",
        "chart": "チャート87 (p.78)",
        "theme": "10月中旬に年中最深の最終ボトム形成、年末年始へ向け【+59%青色上昇波】へ垂直発進",
        "monthly_phase": {
            1: {"phase": "VOLATILITY", "direction": "NEUTRAL", "bias": "年明けの激しいボラティリティ", "score": 0.0},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "春先の調整下落", "score": -1.0},
            3: {"phase": "DOWN", "direction": "DOWN", "bias": "安値模索", "score": -1.0},
            4: {"phase": "REBOUND", "direction": "UP", "bias": "自律反発局面", "score": 0.5},
            5: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "初夏の保ち合い", "score": 0.0},
            6: {"phase": "DOWN", "direction": "DOWN", "bias": "夏季の安値掘り下げ", "score": -1.0},
            7: {"phase": "DOWN", "direction": "DOWN", "bias": "夏枯れ期", "score": -0.5},
            8: {"phase": "DOWN", "direction": "DOWN", "bias": "最終底入れ前段の急落", "score": -1.0},
            9: {"phase": "BOTTOMING", "direction": "BOTTOM", "bias": "年中最深大底の形成ゾーン突入", "score": 1.0},
            10: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【10月中旬大底】年末年始へ向けた【+59%青色上昇波】発進点", "score": 2.5},
            11: {"phase": "RALLY_ACCELERATION", "direction": "UP", "bias": "【+59%上昇波】ショートスクイズ加速期", "score": 2.0},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "年末ターゲット（65ドル超）到達ゾーン", "score": 1.5}
        },
        "tdow_bias": {0: "中立", 1: "中立", 2: "中立", 3: "木曜買い（貴金属連動）", 4: "金曜買い（週末買い優位）"},
        "tdom_best": [1, 15]
    },
    "PL": {
        "asset": "プラチナ (PL)",
        "chart": "チャート86 (p.77)",
        "theme": "2月大底から春に【+54%青色上昇波】急騰、夏押し目から年末高へ",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "年始の調整波", "score": -0.5},
            2: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【2月大底】+54%青色上昇波の起点", "score": 2.0},
            3: {"phase": "RALLY", "direction": "UP", "bias": "産業用需要と買い戻しによる反発", "score": 1.5},
            4: {"phase": "RALLY_PEAK", "direction": "TOP", "bias": "春のピーク到達警戒（+54%達成）", "score": 1.0},
            5: {"phase": "DOWN", "direction": "DOWN", "bias": "初夏の反落調整", "score": -1.0},
            6: {"phase": "DOWN", "direction": "DOWN", "bias": "夏季安値形成", "score": -1.0},
            7: {"phase": "BOTTOMING", "direction": "BOTTOM", "bias": "夏底入れ", "score": 1.0},
            8: {"phase": "RALLY", "direction": "UP", "bias": "秋口の上昇波", "score": 1.5},
            9: {"phase": "PULLBACK", "direction": "DOWN", "bias": "秋の小幅調整", "score": -0.5},
            10: {"phase": "BOTTOMING", "direction": "BOTTOM", "bias": "年末買い準備の底固め", "score": 1.0},
            11: {"phase": "RALLY", "direction": "UP", "bias": "年末産業用実需引き取り", "score": 1.5},
            12: {"phase": "RALLY", "direction": "UP", "bias": "年末年始の上昇トレンド", "score": 1.5}
        },
        "tdow_bias": {0: "中立", 1: "火曜買い", 2: "中立", 3: "木曜買い", 4: "金曜買い"},
        "tdom_best": [1, 12]
    },
    "CL": {
        "asset": "原油 WTI (CL)",
        "chart": "チャート97 (p.85)",
        "theme": "5月大底から初秋へ【+72%青色上昇波】。10年周期安値サイクル通過後の本格上昇",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "冬期暖房需要一巡後の調整下落", "score": -0.5},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "製油所メンテ前の需要減退期", "score": -1.0},
            3: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "春の底固め保ち合い", "score": 0.0},
            4: {"phase": "DOWN", "direction": "DOWN", "bias": "最終ボトムへ向けた急落押し目", "score": -1.0},
            5: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【5月大底】+72%青色上昇波の起点", "score": 2.0},
            6: {"phase": "RALLY", "direction": "UP", "bias": "サマードライブ需要立ち上がり", "score": 1.5},
            7: {"phase": "RALLY", "direction": "UP", "bias": "夏季需要ピーク・在庫引き出し加速", "score": 1.5},
            8: {"phase": "RALLY_ACCELERATION", "direction": "UP", "bias": "【+72%上昇波ピーク接近】", "score": 2.0},
            9: {"phase": "PEAK", "direction": "TOP", "bias": "年間最高値圏到達・利確売り警戒", "score": 0.5},
            10: {"phase": "DOWN", "direction": "DOWN", "bias": "秋の製油所定期修理（メンテナンス）による需要減退", "score": -1.0},
            11: {"phase": "DOWN", "direction": "DOWN", "bias": "冬期前の押し目形成", "score": -0.5},
            12: {"phase": "REBOUND", "direction": "UP", "bias": "冬期暖房油需要への転換自律反発", "score": 1.0}
        },
        "tdow_bias": {0: "中立", 1: "火曜買い", 2: "EIA在庫発表日（ボラティリティ警戒）", 3: "木曜買い", 4: "週末ポジション調整"},
        "tdom_best": [5, 14]
    },
    "NG": {
        "asset": "天然ガス (NG)",
        "chart": "チャート99 (p.86)",
        "theme": "春の+63%上昇波と、10月大底からの冬期【+72%緑色踏み上げ波】",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "厳冬期需要ピークアウトからの下落", "score": -1.0},
            2: {"phase": "MAJOR_BOTTOM_1", "direction": "UP", "bias": "【2月大底】春季+63%青色上昇波の起点", "score": 1.5},
            3: {"phase": "RALLY", "direction": "UP", "bias": "春の在庫注入期前の買い戻し", "score": 1.5},
            4: {"phase": "RALLY", "direction": "UP", "bias": "冷房需要先取り上昇", "score": 1.0},
            5: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "初夏の保ち合い", "score": 0.0},
            6: {"phase": "RALLY", "direction": "UP", "bias": "夏の猛暑冷房需要ピーク", "score": 1.0},
            7: {"phase": "PEAK", "direction": "TOP", "bias": "夏季ピークアウト・在庫積み増し警戒", "score": -0.5},
            8: {"phase": "DOWN", "direction": "DOWN", "bias": "秋口の在庫余剰懸念・急落押し目", "score": -1.5},
            9: {"phase": "DOWN_BOTTOMING", "direction": "BOTTOM", "bias": "年中最安値ゾーン接近・冬相場の仕込み場", "score": 1.0},
            10: {"phase": "MAJOR_BOTTOM_2", "direction": "UP", "bias": "【10月秋底完了】冬の寒波プレミアム【+72%踏み上げ波】点火", "score": 2.5},
            11: {"phase": "RALLY_EXPLOSION", "direction": "UP", "bias": "暖房需要爆発・ショート踏み上げ", "score": 2.5},
            12: {"phase": "WINTER_PEAK", "direction": "TOP", "bias": "厳冬期ターゲット到達・高値利確", "score": 1.5}
        },
        "tdow_bias": {0: "月曜買い", 1: "中立", 2: "中立", 3: "木曜EIA在庫発表後（反転狙い）", 4: "週末ヘッジ買い"},
        "tdom_best": [1, 20]
    },
    "HG": {
        "asset": "銅 (HG)",
        "chart": "チャート82 (p.75)",
        "theme": "6月大底から初夏反発、10月押し目から年末へ【+69%青色上昇波】",
        "monthly_phase": {
            1: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "年初レンジ展開", "score": 0.0},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "春節前後の調整下落", "score": -0.5},
            3: {"phase": "DOWN", "direction": "DOWN", "bias": "世界景況感睨みの安値模索", "score": -1.0},
            4: {"phase": "REBOUND", "direction": "UP", "bias": "自律反発", "score": 0.5},
            5: {"phase": "DOWN", "direction": "DOWN", "bias": "大底へ向けた最終下落", "score": -1.0},
            6: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【6月大底】4.80ドル岩盤からの反転上昇", "score": 2.0},
            7: {"phase": "RALLY", "direction": "UP", "bias": "実需引き取り拡大", "score": 1.5},
            8: {"phase": "RALLY", "direction": "UP", "bias": "夏の上昇波", "score": 1.5},
            9: {"phase": "PULLBACK", "direction": "DOWN", "bias": "秋の急押し目形成", "score": -0.5},
            10: {"phase": "SECONDARY_BOTTOM", "direction": "UP", "bias": "【10月押し目完了】年末へ向けた【+69%青色上昇波】発進", "score": 2.0},
            11: {"phase": "RALLY_ACCELERATION", "direction": "UP", "bias": "年末AI送電網・設備投資実需買い", "score": 2.0},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "年間高値トライ", "score": 1.5}
        },
        "tdow_bias": {0: "月曜買い", 1: "中立", 2: "中立", 3: "木曜買い", 4: "金曜中立"},
        "tdom_best": [1, 10]
    },
    "ZS": {
        "asset": "大豆 (ZS)",
        "chart": "チャート106 (p.93)",
        "theme": "7月大底から全米天候相場【+65%青色上昇波】で10月ピークへ、秋は収穫圧力で下落",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "南米収穫前の軟調地合い", "score": -0.5},
            2: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "保ち合い", "score": 0.0},
            3: {"phase": "DOWN", "direction": "DOWN", "bias": "作付け期前調整", "score": -0.5},
            4: {"phase": "DOWN", "direction": "DOWN", "bias": "米国作付け進捗売り", "score": -1.0},
            5: {"phase": "DOWN", "direction": "DOWN", "bias": "順調な作付けによる安値模索", "score": -1.0},
            6: {"phase": "DOWN", "direction": "DOWN", "bias": "底入れ前段の急落", "score": -1.0},
            7: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【7月大底】全米天候相場【+65%青色上昇波】点火", "score": 2.0},
            8: {"phase": "RALLY_ACCELERATION", "direction": "UP", "bias": "開花・結実期の乾燥リスク急騰", "score": 2.0},
            9: {"phase": "RALLY", "direction": "UP", "bias": "供給不安プレミアム拡大", "score": 1.5},
            10: {"phase": "HARVEST_TOP_TO_DROP", "direction": "TOP_TO_DOWN", "bias": "【10月上旬ピークアウト】全米収穫圧力（Harvest Pressure）による下落波入り", "score": -1.5},
            11: {"phase": "DOWN", "direction": "DOWN", "bias": "全米収穫ピーク・現物投げ売り圧力", "score": -1.5},
            12: {"phase": "BOTTOMING", "direction": "BOTTOM", "bias": "収穫完了による自律反発準備", "score": 0.5}
        },
        "tdow_bias": {0: "中立", 1: "火曜買い", 2: "中立", 3: "木曜売り（収穫期）", 4: "金曜中立"},
        "tdom_best": [2, 11]
    },
    "ZC": {
        "asset": "トウモロコシ (ZC)",
        "chart": "チャート104 (p.92)",
        "theme": "6月大底から年末へ【+74%青色巨大上昇波】。秋の小幅押しを経て12月年間最高値へ",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "年初の軟調地合い", "score": -0.5},
            2: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "保ち合い底固め", "score": 0.0},
            3: {"phase": "DOWN", "direction": "DOWN", "bias": "在庫統計発表前の売り", "score": -0.5},
            4: {"phase": "DOWN", "direction": "DOWN", "bias": "全米作付け進捗による下げ", "score": -1.0},
            5: {"phase": "DOWN", "direction": "DOWN", "bias": "大底へ向けた最終ふるい落とし", "score": -1.0},
            6: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【6月大底】年末へ向けた【+74%青色巨大上昇波】発進", "score": 2.0},
            7: {"phase": "RALLY", "direction": "UP", "bias": "受粉期受難リスクによる天候ラリー", "score": 1.5},
            8: {"phase": "RALLY", "direction": "UP", "bias": "夏の上昇波継続", "score": 1.5},
            9: {"phase": "PULLBACK", "direction": "DOWN", "bias": "新穀収穫初期の一次的な押し目（買い場）", "score": 0.5},
            10: {"phase": "RALLY_RESUME", "direction": "UP", "bias": "収穫売り一巡・エタノール需要急増", "score": 1.5},
            11: {"phase": "RALLY_SURGE", "direction": "UP", "bias": "年末買い需要の本格化", "score": 2.0},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "【12月年間最高値】+74%達成ターゲット圏", "score": 2.0}
        },
        "tdow_bias": {0: "月曜買い", 1: "火曜買い", 2: "中立", 3: "中立", 4: "金曜中立"},
        "tdom_best": [1, 15]
    },
    "ZW": {
        "asset": "小麦 (ZW)",
        "chart": "チャート109 (p.94)",
        "theme": "8月下旬〜9月大底から10月へ【+84%青色垂直急騰波】",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "年初の軟調地合い", "score": -0.5},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "春小麦作付け前の低迷", "score": -0.5},
            3: {"phase": "DOWN", "direction": "DOWN", "bias": "安値圏推移", "score": -0.5},
            4: {"phase": "DOWN", "direction": "DOWN", "bias": "世界供給安定期の下落", "score": -1.0},
            5: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "初夏の保ち合い", "score": 0.0},
            6: {"phase": "DOWN", "direction": "DOWN", "bias": "北半球冬小麦収穫圧力", "score": -1.0},
            7: {"phase": "DOWN", "direction": "DOWN", "bias": "収穫ピーク売り", "score": -1.0},
            8: {"phase": "MAJOR_BOTTOM", "direction": "BOTTOM", "bias": "【8月下旬年中最深ボトム形成】", "score": 1.5},
            9: {"phase": "RALLY_EXPLOSION", "direction": "UP", "bias": "【9月発進】10月へ向けた【+84%青色垂直急騰波】", "score": 2.5},
            10: {"phase": "RALLY_PEAK", "direction": "TOP", "bias": "【10月急騰ピーク】高値達成・利確売り警戒", "score": 0.5},
            11: {"phase": "DOWN", "direction": "DOWN", "bias": "冬小麦作付け進捗・反落調整", "score": -1.0},
            12: {"phase": "REBOUND", "direction": "UP", "bias": "越冬前の自律反発", "score": 1.0}
        },
        "tdow_bias": {0: "月曜買い", 1: "火曜買い", 2: "中立", 3: "中立", 4: "金曜中立"},
        "tdom_best": [3, 18]
    },
    "SB": {
        "asset": "砂糖 (SB)",
        "chart": "チャート94 (p.82)",
        "theme": "3月大底から6月へ【+60%青色上昇波】、8月押し目から年末高へ",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "年初の調整下落", "score": -0.5},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "ブラジル製糖準備期の下落", "score": -1.0},
            3: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【3月大底】14.4セント岩盤からの【+60%上昇波】発進", "score": 2.0},
            4: {"phase": "RALLY", "direction": "UP", "bias": "端境期供給逼迫ラリー", "score": 1.5},
            5: {"phase": "RALLY", "direction": "UP", "bias": "エタノール需要拡大", "score": 1.5},
            6: {"phase": "RALLY_PEAK", "direction": "TOP", "bias": "【6月ピーク】+60%達成水準", "score": 0.5},
            7: {"phase": "DOWN", "direction": "DOWN", "bias": "ブラジル圧搾ピークの売り圧力", "score": -1.0},
            8: {"phase": "SUMMER_BOTTOM", "direction": "BOTTOM", "bias": "8月中旬〜下旬のサマーボトム", "score": 1.5},
            9: {"phase": "RALLY", "direction": "UP", "bias": "秋の実需買い回復", "score": 1.5},
            10: {"phase": "RALLY", "direction": "UP", "bias": "インド輸出規制思惑", "score": 1.5},
            11: {"phase": "PULLBACK", "direction": "DOWN", "bias": "年末前の小幅調整", "score": -0.5},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "年末高値トライ", "score": 1.5}
        },
        "tdow_bias": {0: "中立", 1: "火曜買い", 2: "中立", 3: "木曜買い", 4: "金曜中立"},
        "tdom_best": [1, 14]
    },
    "CT": {
        "asset": "コットン (CT)",
        "chart": "チャート91 (p.81)",
        "theme": "4月下旬〜5月大底から初秋へ【+73%青色上昇波】",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "年明けの調整", "score": -0.5},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "需要減退懸念", "score": -0.5},
            3: {"phase": "DOWN", "direction": "DOWN", "bias": "安値圏推移", "score": -0.5},
            4: {"phase": "DOWN", "direction": "DOWN", "bias": "大底前段の下げ", "score": -1.0},
            5: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【5月大底】61.5セントからの【+73%上昇波】発進", "score": 2.0},
            6: {"phase": "RALLY", "direction": "UP", "bias": "全米生育期天候相場", "score": 1.5},
            7: {"phase": "RALLY", "direction": "UP", "bias": "単収懸念の上昇波", "score": 1.5},
            8: {"phase": "RALLY", "direction": "UP", "bias": "夏の上昇加速", "score": 1.5},
            9: {"phase": "RALLY_PEAK", "direction": "TOP", "bias": "【9月ピーク】+73%達成ターゲット圏", "score": 0.5},
            10: {"phase": "DOWN", "direction": "DOWN", "bias": "テキサス収穫開始による現物売り圧力", "score": -1.0},
            11: {"phase": "DOWN", "direction": "DOWN", "bias": "全米収穫ピーク売り", "score": -1.0},
            12: {"phase": "REBOUND", "direction": "UP", "bias": "収穫完了後の下げ止まり反発", "score": 0.5}
        },
        "tdow_bias": {0: "中立", 1: "火曜買い", 2: "中立", 3: "木曜買い", 4: "金曜中立"},
        "tdom_best": [2, 16]
    },
    "CC": {
        "asset": "ココア (CC)",
        "chart": "チャート89 (p.80)",
        "theme": "3月大底から初夏へ【+90%青色巨大上昇波】（4600から7300へ大暴騰）",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "メインクロップ出荷期の軟調地合い", "score": -0.5},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "出荷進捗による調整", "score": -0.5},
            3: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【3月大底】4600ドルからの【+90%青色上昇波】点火", "score": 2.5},
            4: {"phase": "RALLY_SURGE", "direction": "UP", "bias": "西アフリカ減産・構造的供給不足ラリー", "score": 2.5},
            5: {"phase": "RALLY_SURGE", "direction": "UP", "bias": "ショート踏み上げ加速", "score": 2.5},
            6: {"phase": "RALLY_SURGE", "direction": "UP", "bias": "7000ドル突破猛騰波", "score": 2.0},
            7: {"phase": "RALLY_PEAK", "direction": "TOP", "bias": "【7月ピーク】+90%達成水準（7300ドル）", "score": 0.5},
            8: {"phase": "DOWN", "direction": "DOWN", "bias": "夏枯れ高値警戒・急落調整", "score": -1.5},
            9: {"phase": "DOWN", "direction": "DOWN", "bias": "中間期安値形成", "score": -1.5},
            10: {"phase": "BOTTOMING", "direction": "BOTTOM", "bias": "秋のメインクロップ前底入れ・買い場", "score": 1.5},
            11: {"phase": "RALLY", "direction": "UP", "bias": "クリスマス菓子実需買い", "score": 1.5},
            12: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "高値保ち合い", "score": 0.5}
        },
        "tdow_bias": {0: "月曜買い", 1: "中立", 2: "中立", 3: "木曜買い", 4: "金曜中立"},
        "tdom_best": [1, 15]
    },
    "KC": {
        "asset": "コーヒー (KC)",
        "chart": "チャート90 (p.80)",
        "theme": "8月下旬〜9月大底から年末へ【+68%青色上昇波】（370から430超へ）",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "ブラジル天候安定による押し目", "score": -0.5},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "調整下落", "score": -0.5},
            3: {"phase": "DOWN", "direction": "DOWN", "bias": "春先安値模索", "score": -0.5},
            4: {"phase": "REBOUND", "direction": "UP", "bias": "開花期前の自律反発", "score": 0.5},
            5: {"phase": "DOWN", "direction": "DOWN", "bias": "収穫初期の売り圧力", "score": -0.5},
            6: {"phase": "DOWN", "direction": "DOWN", "bias": "ブラジル収穫進捗の下落", "score": -1.0},
            7: {"phase": "DOWN", "direction": "DOWN", "bias": "夏季安値形成", "score": -1.0},
            8: {"phase": "MAJOR_BOTTOM", "direction": "BOTTOM", "bias": "【8月下旬大底形成】370セント岩盤接近", "score": 1.5},
            9: {"phase": "RALLY_EXPLOSION", "direction": "UP", "bias": "【9月発進】年末へ向けた【+68%青色上昇波】点火", "score": 2.5},
            10: {"phase": "RALLY_ACCELERATION", "direction": "UP", "bias": "ブラジル開花期降雨不足リスク急騰", "score": 2.0},
            11: {"phase": "RALLY", "direction": "UP", "bias": "欧米冬期消費ピーク実需買い", "score": 1.5},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "【12月高値】+68%達成（430セント超）", "score": 1.5}
        },
        "tdow_bias": {0: "月曜買い", 1: "火曜買い", 2: "中立", 3: "木曜買い", 4: "金曜中立"},
        "tdom_best": [2, 17]
    },
    "HE": {
        "asset": "豚肉 (HE)",
        "chart": "チャート103 (p.90)",
        "theme": "春の+72%急騰波、および10月下旬年中最深大底からの年末ハム実需・春先需要急反発",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "年始の出荷増による軟調地合い", "score": -0.5},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "春先の底固め期", "score": -0.5},
            3: {"phase": "MAJOR_BOTTOM_1", "direction": "UP", "bias": "【3月大底】春季+72%青色上昇波の起点", "score": 2.0},
            4: {"phase": "RALLY", "direction": "UP", "bias": "BBQシーズン先取り需要", "score": 1.5},
            5: {"phase": "RALLY", "direction": "UP", "bias": "初夏の実需買い拡大", "score": 1.5},
            6: {"phase": "RALLY_PEAK", "direction": "TOP", "bias": "夏季高値達成（+72%水準）", "score": 1.0},
            7: {"phase": "DOWN", "direction": "DOWN", "bias": "夏枯れ反落", "score": -1.0},
            8: {"phase": "DOWN", "direction": "DOWN", "bias": "秋の過剰出荷（ヘビーピッグ）売り圧力", "score": -1.5},
            9: {"phase": "DOWN", "direction": "DOWN", "bias": "枝肉カットアウト急落・安値圏突入", "score": -1.5},
            10: {"phase": "MAJOR_BOTTOM_2", "direction": "UP", "bias": "【10月下旬年中最深大底】全米特売拡大と年末ハム実需の買い場", "score": 2.5},
            11: {"phase": "RALLY", "direction": "UP", "bias": "過剰出荷一巡・実需納品買い反発", "score": 2.0},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "年末ハム需要ピーク・反発完了", "score": 1.5}
        },
        "tdow_bias": {0: "月曜買い（寄り付き押し目買い）", 1: "火曜買い", 2: "中立", 3: "木曜買い", 4: "金曜中立"},
        "tdom_best": [1, 14]
    },
    "LE": {
        "asset": "生牛 (LE)",
        "chart": "チャート102 (p.89)",
        "theme": "6月下旬〜7月大底から秋へ【+75%青色上昇波】（205から245へ）",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "年始の需要一巡による押し目", "score": -0.5},
            2: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "春先の保ち合い", "score": 0.0},
            3: {"phase": "DOWN", "direction": "DOWN", "bias": "パッカーマージン悪化の下げ", "score": -0.5},
            4: {"phase": "DOWN", "direction": "DOWN", "bias": "フィードロット出荷進捗", "score": -1.0},
            5: {"phase": "DOWN", "direction": "DOWN", "bias": "安値掘り下げ", "score": -1.0},
            6: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【6月下旬大底】全米飼育頭数不足からの【+75%青色上昇波】点火", "score": 2.0},
            7: {"phase": "RALLY", "direction": "UP", "bias": "BBQ・ステーキ需要本格化", "score": 1.5},
            8: {"phase": "RALLY", "direction": "UP", "bias": "現物カットアウト上昇連動", "score": 1.5},
            9: {"phase": "RALLY", "direction": "UP", "bias": "感謝祭向け前倒し買い", "score": 1.5},
            10: {"phase": "RALLY_PEAK", "direction": "TOP", "bias": "【10月ピーク】+75%達成ターゲット圏（245ドル）", "score": 0.5},
            11: {"phase": "DOWN", "direction": "DOWN", "bias": "感謝祭直後の手仕舞い売り", "score": -1.0},
            12: {"phase": "REBOUND", "direction": "UP", "bias": "年末高アノマリーの自律反発", "score": 1.0}
        },
        "tdow_bias": {0: "月曜買い", 1: "火曜買い", 2: "中立", 3: "木曜中立", 4: "金曜中立"},
        "tdom_best": [1, 12]
    },
    "DXY": {
        "asset": "ドルインデックス (DXY)",
        "chart": "チャート74 (p.69)",
        "theme": "5月大底から初秋へ【+70%青色上昇波】（97.4から100.4へ）。秋以降はドル安基調",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "年始のドル売り基調", "score": -0.5},
            2: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "金利見通し睨みの保ち合い", "score": 0.0},
            3: {"phase": "DOWN", "direction": "DOWN", "bias": "利下げ観測による下落", "score": -0.5},
            4: {"phase": "DOWN", "direction": "DOWN", "bias": "大底へ向けた最終安値模索", "score": -1.0},
            5: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【5月大底】97.4からの【+70%上昇波】スタート", "score": 1.5},
            6: {"phase": "RALLY", "direction": "UP", "bias": "米景気底堅さによるドル買い戻し", "score": 1.5},
            7: {"phase": "RALLY", "direction": "UP", "bias": "夏の上昇波継続", "score": 1.5},
            8: {"phase": "RALLY_PEAK", "direction": "TOP", "bias": "【8月下旬〜9月上旬ピーク】100.4到達・天井警戒", "score": 0.0},
            9: {"phase": "DOWN_START", "direction": "DOWN", "bias": "秋のドル売り転換", "score": -1.0},
            10: {"phase": "DOWN", "direction": "DOWN", "bias": "年末利下げ織り込みのドル安トレンド", "score": -1.5},
            11: {"phase": "DOWN", "direction": "DOWN", "bias": "リパトリ一巡後のドル安継続", "score": -1.0},
            12: {"phase": "DOWN", "direction": "DOWN", "bias": "年末ドル需要一巡の軟調地合い", "score": -1.0}
        },
        "tdow_bias": {0: "中立", 1: "火曜買い", 2: "中立", 3: "木曜中立", 4: "金曜中立"},
        "tdom_best": [1, 15]
    },
    "ZN": {
        "asset": "米10年債 (ZN)",
        "chart": "チャート70 (p.66)",
        "theme": "初夏大底から秋・年末へ【+74%青色上昇波】（利回り低下＝債券価格急騰）",
        "monthly_phase": {
            1: {"phase": "DOWN", "direction": "DOWN", "bias": "年初の国債発行圧力", "score": -0.5},
            2: {"phase": "DOWN", "direction": "DOWN", "bias": "インフレ警戒による利回り上昇・債券安", "score": -0.5},
            3: {"phase": "RANGE", "direction": "NEUTRAL", "bias": "保ち合い", "score": 0.0},
            4: {"phase": "DOWN", "direction": "DOWN", "bias": "安値模索", "score": -0.5},
            5: {"phase": "DOWN", "direction": "DOWN", "bias": "大底へ向けた押し目", "score": -1.0},
            6: {"phase": "MAJOR_BOTTOM", "direction": "UP", "bias": "【6月大底】111.8からの【+74%上昇波】スタート", "score": 2.0},
            7: {"phase": "RALLY", "direction": "UP", "bias": "利下げ期待による反発", "score": 1.5},
            8: {"phase": "RALLY", "direction": "UP", "bias": "夏の上昇波", "score": 1.5},
            9: {"phase": "SECONDARY_BOTTOM", "direction": "UP", "bias": "9月押し目完了からの第2上昇波", "score": 1.5},
            10: {"phase": "RALLY_ACCELERATION", "direction": "UP", "bias": "質への逃避（Flight to Quality）買い加速", "score": 2.0},
            11: {"phase": "RALLY", "direction": "UP", "bias": "利下げ織り込み進行", "score": 1.5},
            12: {"phase": "YEAR_END_PEAK", "direction": "UP", "bias": "【12月高値】+74%達成ターゲット圏", "score": 2.0}
        },
        "tdow_bias": {0: "中立", 1: "火曜中立", 2: "水曜最弱（週の中だるみ）", 3: "木曜後半から上昇反発", 4: "金曜買い（最強買い日・週末買いバイアス）"},
        "tdom_best": [16, 17, 18, 19, 20, 21]  # TDOM 21 勝率77.8%
    }
}


# --- 2. 成田博之氏 カレンダー換算特異日データベース ---
# 金先物（GC）の高勝率アノマリー日
NARITA_GOLD_SPECIAL_DATES = {
    "01-07": "TDOY 4: 金先物 年初買い特異日（1/7）",
    "01-08": "TDOY 5: 金先物 年初買い特異日（1/8）",
    "01-09": "TDOY 6: 金先物 年初買い特異日（1/9）",
    "01-15": "TDOY 10: 金先物 押し目買い特異日（1/15）",
    "01-16": "TDOY 11: 金先物 買い特異日（1/16）",
    "01-27": "TDOY 17: 金先物 買い特異日（1/27）",
    "01-29": "TDOY 19: 金先物 月末買い特異日（1/29）",
    "02-04": "TDOY 23: 金先物 2月買い特異日（2/4）",
    "02-17": "TDOY 31: 金先物 2月中旬買い特異日（2/17）",
    "02-20": "TDOY 34: 金先物 2月下旬買い特異日（2/20）",
    "03-30": "TDOY 60: 金先物 4月上昇波前夜の買い特異日（3/30）",
    "04-02": "TDOY 63: 金先物 +72%青色上昇波初動 買い特異日（4/2）",
    "04-07": "TDOY 65: 金先物 4月急騰買い特異日（4/7）",
    "04-08": "TDOY 66: 金先物 4月急騰買い特異日（4/8）",
    "04-09": "TDOY 67: 金先物 4月急騰買い特異日（4/9）",
    "05-28": "TDOY 101: 金先物 初夏ピーク前買い特異日（5/28）",
    "07-09": "TDOY 129: 金先物 夏枯れ反発買い特異日（7/9）",
    "07-22": "TDOY 138: 金先物 7月下旬買い特異日（7/22）",
    "07-28": "TDOY 142: 金先物 7月末買い特異日（7/28）",
    "08-20": "TDOY 159: 金先物 8月夏底完了買い特異日（8/20）",
    "08-21": "TDOY 160: 金先物 8月夏底反発買い特異日（8/21）",
    "08-27": "TDOY 164: 金先物 秋相場スタート買い特異日（8/27）",
    "12-16": "TDOY 241: 金先物 年末ラリー買い特異日（12/16）",
    "12-18": "TDOY 243: 金先物 年末ラリー買い特異日（12/18）",
    "12-31": "TDOY 251: 金先物 年末最終日買い特異日（12/31）"
}


def calculate_tdom(dt: datetime) -> int:
    """Calculates approximate Trading Day of the Month (ignoring weekends)"""
    count = 0
    for day in range(1, dt.day + 1):
        test_d = date(dt.year, dt.month, day)
        if test_d.weekday() < 5:  # Mon to Fri
            count += 1
    return count


def evaluate_larry_forecast(sym: str, dt: datetime = None) -> dict:
    """
    Evaluates Larry Williams 2026 Forecast for a given asset on a specific date.
    Returns quantitative score delta, cycle stage, TDOW/TDOM alerts, and narrative commentary.
    """
    if dt is None:
        jst = timezone(timedelta(hours=9))
        dt = datetime.now(jst)

    cycle_info = LARRY_2026_CYCLES.get(sym)
    if not cycle_info:
        return {}

    month = dt.month
    weekday = dt.weekday()  # 0=Mon, 1=Tue, ..., 4=Fri
    tdom = calculate_tdom(dt)
    month_day_str = dt.strftime("%m-%d")

    # 1. 2026 Cycle Phase Evaluation
    monthly_data = cycle_info["monthly_phase"].get(month, {})
    cycle_score = monthly_data.get("score", 0.0)
    cycle_direction = monthly_data.get("direction", "NEUTRAL")
    cycle_bias_desc = monthly_data.get("bias", "")
    theme = cycle_info.get("theme", "")
    chart_ref = cycle_info.get("chart", "")

    signals = []
    signals.append(f"【2026年数理サイクル】{chart_ref}: {cycle_bias_desc}")

    # 2. TDOW (Day of Week) Evaluation
    tdow_desc = cycle_info.get("tdow_bias", {}).get(weekday, "中立")
    tdow_bonus = 0.0
    if "最強" in tdow_desc or "81%" in tdow_desc:
        tdow_bonus += 0.8
        signals.append(f"【曜日アノマリー（TDOW）】本日{tdow_desc}（勝率最高峰の追い風）")
    elif "買い" in tdow_desc and "売り" not in tdow_desc:
        tdow_bonus += 0.5
        signals.append(f"【曜日アノマリー（TDOW）】本日{tdow_desc}（上昇バイアス）")
    elif "最弱" in tdow_desc or "下落" in tdow_desc:
        tdow_bonus -= 0.5
        signals.append(f"【曜日アノマリー（TDOW）】本日{tdow_desc}（週内調整警戒）")

    # 3. TDOM (Trading Day of Month) Evaluation
    tdom_best = cycle_info.get("tdom_best", [])
    tdom_alert = ""
    tdom_bonus = 0.0
    if tdom in tdom_best:
        tdom_bonus += 0.7
        tdom_alert = f"🌟 本日は月の第{tdom}取引日（TDOM {tdom}：歴史的高勝率エントリー日）"
        signals.append(f"【日柄アノマリー（TDOM）】{tdom_alert}")
    elif tdom == 1:
        tdom_bonus += 0.5
        tdom_alert = "月初取引日（TDOM 1：伝統的月次買いバイアス）"
        signals.append(f"【日柄アノマリー（TDOM）】{tdom_alert}")

    # Special S&P 500 Rule: TDOM 10 on Monday or TDOM 15 on Monday (Win rate 81%)
    if sym in ["ES", "NQ"] and weekday == 0 and tdom in [10, 15]:
        tdom_bonus += 1.5
        signals.append(f"🔥【ラリー特別シグナル】月の第{tdom}取引日の月曜日（実戦検証勝率81%の神日柄）発火！")

    # Special Gold Rule: TDOM 6 on Tuesday (Win rate 77%)
    if sym == "GC" and weekday == 1 and tdom == 6:
        tdom_bonus += 1.5
        signals.append(f"🔥【ラリー特別シグナル】月の第6取引日の火曜日（金先物 勝率77%の神日柄）発火！")

    # Special Bond Rule: TDOM 6 on Tuesday (Win rate 77%) or TDOM 21 (Win rate 77.8%)
    if sym == "ZN" and weekday == 1 and tdom == 6:
        tdom_bonus += 1.5
        signals.append(f"🔥【ラリー特別シグナル】月の第6取引日の火曜日（米国債 勝率77%の神日柄）発火！")
    elif sym == "ZN" and tdom == 21:
        tdom_bonus += 1.0
        signals.append(f"🔥【ラリー特別シグナル】月の第21取引日（米国債 過去194回中 勝率77.8%の最強日柄）！")

    # 4. Narita Special Calendar Dates Check
    special_date_alert = ""
    if sym == "GC" and month_day_str in NARITA_GOLD_SPECIAL_DATES:
        special_date_alert = NARITA_GOLD_SPECIAL_DATES[month_day_str]
        tdom_bonus += 1.0
        signals.append(f"🌟【成田式カレンダー特異日】{special_date_alert}")

    total_larry_score = round(cycle_score + tdow_bonus + tdom_bonus, 2)

    return {
        "symbol": sym,
        "date_str": dt.strftime("%Y-%m-%d"),
        "month": month,
        "weekday": weekday,
        "tdom": tdom,
        "chart_ref": chart_ref,
        "theme": theme,
        "cycle_phase": monthly_data.get("phase", "UNKNOWN"),
        "cycle_direction": cycle_direction,
        "cycle_bias_desc": cycle_bias_desc,
        "cycle_score": cycle_score,
        "tdow_desc": tdow_desc,
        "tdow_bonus": tdow_bonus,
        "tdom_alert": tdom_alert,
        "tdom_bonus": tdom_bonus,
        "special_date_alert": special_date_alert,
        "total_larry_score": total_larry_score,
        "larry_signals": signals
    }


if __name__ == "__main__":
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    print(f"Testing Larry Forecast Engine for {now.strftime('%Y-%m-%d %H:%M:%S JST')}:")
    for s in ["ES", "GC", "SI", "CL", "NG", "HE", "ZN"]:
        res = evaluate_larry_forecast(s, now)
        print(f"[{s}] Score: {res['total_larry_score']:+0.1f} | Phase: {res['cycle_phase']} | {res['cycle_bias_desc'][:40]}")
        for sig in res['larry_signals']:
            print(f"   -> {sig}")
