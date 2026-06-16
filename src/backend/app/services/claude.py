from anthropic import AsyncAnthropic

from app.core.config import settings

_SYSTEM_REFINE_PROMPT = """\
あなたは地方創生DXの専門コンサルタントです。
既存の提案書に対してクライアントからの追加指示を受け、提案書を更新してください。

更新後の提案書は必ず完全な形（全セクション含む）で出力してください。
「## 提案する施策・ソリューション」の施策一覧表（①②③④の丸数字付き）を必ず含めてください。
Markdown形式で見出し・箇条書き・表を適切に使用してください。
"""

_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

_SYSTEM_PROMPT = """\
あなたは地方創生DXの専門コンサルタントです。
日本の自治体向けに、データ活用・デジタル化を通じた地域課題解決の提案書を作成します。

【初回提案書の構成】
1. 実現したい将来像（入力内容を整理）
2. 現状分析（現在像・課題・原因）
3. 提案する施策・ソリューション（①②③④の一覧表）
4. 提案する施策・ソリューションの個別具体（各施策の概要・見積もり）

施策は必ず ① ② ③ ④ の丸数字を使い、
「## 提案する施策・ソリューション」に一覧表、
「## 提案する施策・ソリューションの個別具体」に ### ①〜### ④ の個別セクションを作成してください。

Markdown形式で見出し・箇条書き・表を適切に使用してください。
"""

_SYSTEM_DEEPEN_PROMPT = """\
あなたは地方創生DXの専門コンサルタントです。
選択された施策について、以下の構成で詳細実施計画を作成してください。

各施策について必ず:
1. 解決する課題と目標年度（現状を〇〇年で解決）
2. 定量的な将来像（推定数値を含む表）
3. 実施アクション（具体的なステップ）
4. 実現までのロードマップ（マイルストーン付き）
5. 出典・参照（図表の根拠となるURL）

Markdown形式で詳細に記述してください。
"""

# ─────────────────────────────────────────────
# デモ用固定施策定義
# ─────────────────────────────────────────────

# 別案用の代替施策セット
_ALT_DEMO_MEASURES = [
    (1, "①", "子育て支援DX（保育申請・学校連絡デジタル化）",    "★★★", "2,500万円"),
    (2, "②", "防災・インフラ管理DX（IoTセンサー・BIM導入）",    "★★★", "6,000万円"),
    (3, "③", "農業・産業振興DX（スマート農業・販路拡大支援）",   "★★",  "3,000万円"),
    (4, "④", "観光・地域プロモーションDX（デジタルコンテンツ）", "★★",  "2,000万円"),
]

_DEMO_MEASURES = [
    (1, "①", "電子申請・窓口DX",                  "★★★", "5,000万円"),
    (2, "②", "データ活用・分析基盤整備",            "★★★", "3,000万円"),
    (3, "③", "AIチャットボット・市民サービス強化",   "★★",  "1,500万円"),
    (4, "④", "職員DXリテラシー向上プログラム",      "★★",  "500万円"),
]

_MEASURE_DETAILS = {
    1: {
        "summary": "全行政手続きのオンライン化により窓口来庁率を大幅削減。マイナンバーカードを活用した本人確認基盤を整備し、市民がいつでもどこからでも申請できる環境を構築します。",
        "features": [
            "マイナンバーカード認証基盤の導入",
            "申請フォームの標準化・デジタル化（対象：全250種類の手続き）",
            "バックオフィスシステムとのAPI連携",
            "申請状況リアルタイム確認機能",
        ],
        "estimate": [
            ("システム開発費", "3,500万円"),
            ("導入・設定費", "800万円"),
            ("初年度保守費", "700万円"),
            ("**合計**", "**5,000万円**"),
        ],
        "kpi": [("オンライン申請率", "15%", "50%", "75%"), ("窓口来庁数（月間）", "12,000件", "6,000件", "3,000件"), ("年間コスト削減", "—", "2,000万円", "5,000万円")],
        "actions": [
            ("現状調査・要件定義（1〜2ヶ月）", ["全申請手続き（250種）のデジタル化優先度評価", "利用者ヒアリング（市民・職員各50名）", "ベンダー市場調査・RFP作成"]),
            ("システム設計・開発（3〜6ヶ月）", ["マイナンバー認証基盤の構築", "申請フォームビルダーの整備", "セキュリティ審査・脆弱性診断"]),
            ("パイロット導入・検証（2〜3ヶ月）", ["利用率上位10手続きで先行運用", "市民フィードバック収集と改善", "KPI実績の測定"]),
            ("全庁展開・定着化（6〜12ヶ月）", ["全部署への順次ロールアウト", "職員トレーニング・マニュアル整備", "市民向け周知・サポート体制整備"]),
        ],
        "roadmap": [
            ("2025 Q1", "現状調査・要件定義・ベンダー選定"),
            ("2025 Q2", "設計・開発フェーズ開始"),
            ("2025 Q3", "プロトタイプ完成・テスト運用"),
            ("2025 Q4 ✓", "パイロット導入（対象：市民課・税務課）\n         → マイルストーン：パイロット利用率30%達成"),
            ("2026 Q1", "市民向け広報・デジタルサポート窓口開設"),
            ("2026 Q2-Q3 ✓", "全庁展開（全250手続き対応完了）\n         → マイルストーン：オンライン申請率50%達成"),
            ("2026 Q4", "効果測定・改善施策の実施"),
            ("2027 Q1 ✓", "最終評価\n         → 最終目標：オンライン申請率75%達成"),
        ],
        "refs": [
            ("デジタル庁「自治体DX推進計画（第2.2版）」", "https://www.digital.go.jp/policies/local_governments/"),
            ("総務省「自治体DX・情報化推進概要」", "https://www.soumu.go.jp/denshijiti/"),
            ("先進事例：東京都豊島区 電子申請（2023年度 窓口来庁数47%削減）", "https://www.city.toshima.lg.jp/"),
        ],
    },
    2: {
        "summary": "庁内に散在するデータを一元管理・可視化するプラットフォームを構築。政策立案のエビデンスベース化とKPIモニタリングを実現します。",
        "features": [
            "庁内データレイク基盤の整備（人口・財政・福祉・インフラデータの統合）",
            "BIダッシュボードによるリアルタイム可視化",
            "政策効果測定・シミュレーション機能",
            "オープンデータポータルの整備",
        ],
        "estimate": [
            ("データ基盤構築費", "2,000万円"),
            ("BIツール・ライセンス費（3年分）", "600万円"),
            ("導入支援・研修費", "400万円"),
            ("**合計**", "**3,000万円**"),
        ],
        "kpi": [("データ活用部署数", "2課", "10課", "全課"), ("政策効果測定実施率", "5%", "40%", "80%"), ("年間意思決定時間削減", "—", "1,500時間", "4,000時間")],
        "actions": [
            ("現状調査・要件定義（1〜2ヶ月）", ["データ棚卸し・品質評価", "利用部署ヒアリング", "既存システムとの連携設計"]),
            ("基盤構築・データ整備（4〜6ヶ月）", ["データレイク基盤の構築", "ETLパイプラインの整備", "マスターデータ管理の確立"]),
            ("BIダッシュボード開発（2〜3ヶ月）", ["主要KPIダッシュボード（10種）の開発", "ユーザーテストと改善", "職員向けBI研修"]),
            ("運用・拡張（継続）", ["新規データソースの追加対応", "オープンデータ公開", "政策立案支援への活用拡大"]),
        ],
        "roadmap": [
            ("2025 Q1", "データ棚卸・要件定義"),
            ("2025 Q2-Q3", "データ基盤構築・ETL整備"),
            ("2025 Q4 ✓", "パイロット運用（財政・人口部門）\n         → マイルストーン：5KPIのリアルタイム可視化"),
            ("2026 Q1", "BIダッシュボード全10種リリース"),
            ("2026 Q2 ✓", "全課展開完了\n         → マイルストーン：データ活用部署数10課達成"),
            ("2026 Q3-Q4", "オープンデータポータル公開"),
            ("2027 Q1 ✓", "最終評価\n         → 最終目標：政策効果測定実施率80%達成"),
        ],
        "refs": [
            ("デジタル庁「データ戦略」", "https://www.digital.go.jp/policies/data_strategy/"),
            ("総務省「地域情報化アドバイザー制度」", "https://www.soumu.go.jp/denshijiti/advisor.html"),
            ("先進事例：神奈川県相模原市 データ分析基盤", "https://www.city.sagamihara.kanagawa.jp/"),
        ],
    },
    3: {
        "summary": "AIチャットボットによる24時間365日の市民問い合わせ対応を実現。職員の問い合わせ対応工数を削減し、より付加価値の高い業務に集中できる環境を整備します。",
        "features": [
            "FAQ自動応答AIチャットボット（対応言語：日本語・英語・やさしい日本語）",
            "多言語対応・音声入力機能",
            "手続き案内・申請書類の自動案内",
            "チャットログ分析による問い合わせ傾向把握",
        ],
        "estimate": [
            ("AIチャットボット導入費", "800万円"),
            ("初期学習データ整備費", "400万円"),
            ("初年度保守・改善費", "300万円"),
            ("**合計**", "**1,500万円**"),
        ],
        "kpi": [("問い合わせ自動解決率", "0%", "50%", "70%"), ("職員問い合わせ対応時間削減", "—", "2,000時間/年", "5,000時間/年"), ("市民満足度", "65%", "75%", "85%")],
        "actions": [
            ("FAQデータ整備・学習（1〜2ヶ月）", ["よくある問い合わせ1,000件のデータ化", "回答テンプレートの整備", "AIモデルの学習・チューニング"]),
            ("システム導入・テスト（2〜3ヶ月）", ["ウェブサイト・LINEへのチャットボット統合", "多言語対応設定", "庁内テスト・品質確認"]),
            ("本番運用・改善（継続）", ["月次ログ分析・回答精度向上", "新規FAQの追加対応", "音声入力機能の追加"]),
        ],
        "roadmap": [
            ("2025 Q1", "FAQ整備・AIモデル学習"),
            ("2025 Q2 ✓", "チャットボット試験運用開始\n         → マイルストーン：自動解決率30%達成"),
            ("2025 Q3", "LINE・アプリへの展開"),
            ("2025 Q4 ✓", "多言語対応リリース\n         → マイルストーン：月間利用件数1,000件突破"),
            ("2026 Q1-Q2", "音声入力・AI精度向上"),
            ("2026 Q3 ✓", "最終評価\n         → 最終目標：問い合わせ自動解決率70%達成"),
        ],
        "refs": [
            ("デジタル庁「行政サービスのデジタル化」", "https://www.digital.go.jp/policies/services/"),
            ("先進事例：横浜市 AIチャットボット（月間5万件対応）", "https://www.city.yokohama.lg.jp/"),
            ("LINE「自治体向けソリューション」", "https://www.lycbiz.com/jp/service/line-official-account/local-government/"),
        ],
    },
    4: {
        "summary": "職員一人ひとりのDXリテラシーを体系的に向上させるプログラム。ツール活用だけでなく、業務改善思考の醸成を目指します。",
        "features": [
            "DXリテラシー研修（e-ラーニング＋集合研修）",
            "DX推進リーダー育成プログラム（各部署1名）",
            "業務改善ワークショップ（RPA・ノーコードツール活用）",
            "成果発表会・ベストプラクティス共有",
        ],
        "estimate": [
            ("研修コンテンツ開発費", "200万円"),
            ("e-ラーニングプラットフォーム費（3年）", "150万円"),
            ("外部講師・ファシリテーター費", "150万円"),
            ("**合計**", "**500万円**"),
        ],
        "kpi": [("DXリテラシー研修受講率", "0%", "60%", "95%"), ("業務改善提案件数（年間）", "5件", "30件", "80件"), ("RPA等ツール活用部署数", "1課", "5課", "全課")],
        "actions": [
            ("研修設計・コンテンツ開発（1〜2ヶ月）", ["スキルレベル診断ツールの整備", "e-ラーニングコンテンツ（基礎・応用・発展）の開発", "DXリーダー育成カリキュラムの設計"]),
            ("研修実施・DXリーダー育成（6〜12ヶ月）", ["全職員e-ラーニング受講（自己学習）", "集合研修（ノーコードツール・RPA体験）", "各部署DXリーダー（30名）の集中育成"]),
            ("業務改善実践・展開（継続）", ["DXリーダーによる部署内改善活動支援", "四半期ごとの成果発表会", "優良事例の全庁共有"]),
        ],
        "roadmap": [
            ("2025 Q1", "研修コンテンツ開発・プラットフォーム選定"),
            ("2025 Q2 ✓", "e-ラーニング開始・DXリーダー育成スタート\n         → マイルストーン：受講率30%達成"),
            ("2025 Q3", "集合研修・ワークショップ実施"),
            ("2025 Q4 ✓", "DXリーダー30名育成完了\n         → マイルストーン：業務改善提案30件達成"),
            ("2026 Q1-Q2", "業務改善活動の本格展開"),
            ("2026 Q3 ✓", "最終評価\n         → 最終目標：受講率95%・RPA活用全課達成"),
        ],
        "refs": [
            ("デジタル庁「デジタル推進委員」", "https://www.digital.go.jp/policies/digital_supporters/"),
            ("総務省「ICT人材育成」", "https://www.soumu.go.jp/main_sosiki/joho_tsusin/policyreports/joho_tsusin/"),
            ("先進事例：静岡県浜松市 DX人材育成（全職員研修）", "https://www.city.hamamatsu.shizuoka.jp/"),
        ],
    },
}


# ─────────────────────────────────────────────
# デモ提案書ビルダー
# ─────────────────────────────────────────────

def _build_demo_proposal(
    municipality_name: str,
    future_vision: str,
    current_state: str,
    challenges: str,
    root_causes: str,
    url_contents: list[tuple[str, str]],
    attachment_texts: list[tuple[str, str]],
) -> str:
    lines: list[str] = [
        f"# {municipality_name} 地方創生DX提案書",
        "",
        "## 実現したい将来像",
        future_vision or "（未記入）",
        "",
        "## 現状分析",
        "",
        "### 現在の状況",
        current_state or "（未記入）",
        "",
        "### 抱えている課題",
        challenges or "（未記入）",
        "",
        "### 課題の原因",
        root_causes or "（未記入）",
        "",
    ]

    if attachment_texts:
        lines += ["## 添付資料", ""]
        for fname, text in attachment_texts:
            lines.append(f"### {fname}")
            preview = text[:300].strip()
            if preview:
                lines.append(preview + ("…" if len(text) > 300 else ""))
            lines.append("")

    if url_contents:
        lines += ["## 参照URL", ""]
        for url, content in url_contents:
            lines.append(f"### {url}")
            preview = content[:300].strip()
            if preview:
                lines.append(preview + ("…" if len(content) > 300 else ""))
            lines.append("")

    # ── 施策一覧表
    lines += [
        "---",
        "",
        "## 提案する施策・ソリューション",
        "",
        "以下の4施策を提案します。導入目的・優先度・概算費用を整理しました。",
        "",
        "| 番号 | 施策名 | 優先度 | 概算費用 |",
        "|------|--------|--------|---------|",
    ]
    for _, num, title, priority, cost in _DEMO_MEASURES:
        lines.append(f"| {num} | {title} | {priority} | {cost} |")
    lines.append("")

    # ── 個別具体セクション
    lines += [
        "---",
        "",
        "## 提案する施策・ソリューションの個別具体",
        "",
    ]
    for idx, num, title, _, cost in _DEMO_MEASURES:
        d = _MEASURE_DETAILS[idx]
        lines += [
            f"### {num} {title}",
            "",
            "**概要**",
            d["summary"],
            "",
            "**主な機能・内容**",
        ]
        for f in d["features"]:
            lines.append(f"- {f}")
        lines += [
            "",
            "**見積もり**",
            "",
            "| 項目 | 金額 |",
            "|------|------|",
        ]
        for item, amount in d["estimate"]:
            lines.append(f"| {item} | {amount} |")
        lines += ["", "---", ""]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# デモ深掘りビルダー
# ─────────────────────────────────────────────

def _build_demo_deepen(
    municipality_name: str,
    selected_measures: list[tuple[int, str]],
) -> str:
    lines: list[str] = [
        "# 採用施策 詳細実施計画",
        "",
        f"**対象自治体**: {municipality_name}",
        "",
    ]

    circle_map = "①②③④⑤⑥⑦⑧⑨⑩"

    for index, title in selected_measures:
        num = circle_map[index - 1] if 1 <= index <= len(circle_map) else f"({index})"
        d = _MEASURE_DETAILS.get(index)

        lines += [
            "---",
            "",
            f"## {num} {title} ／ 詳細実施計画",
            "",
        ]

        if d:
            # 課題と目標
            lines += [
                "### 解決する課題と目標年度",
                "",
                f"**現状**: {municipality_name}における {title} 領域の非効率・デジタル格差",
                "**目標**: 2027年3月末までに本施策の主要KPIを達成",
                "",
                "### 定量的な将来像（推定）",
                "",
                "| 指標 | 現状 | 導入1年後 | 導入3年後 |",
                "|------|------|----------|----------|",
            ]
            for row in d["kpi"]:
                lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |")
            lines.append("")

            # 実施アクション
            lines += ["### 実施アクション", ""]
            for step_title, items in d["actions"]:
                lines.append(f"**{step_title}**")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")

            # ロードマップ
            lines += [
                "### 実現までのロードマップ",
                "",
                "```",
            ]
            for period, desc in d["roadmap"]:
                lines.append(f"{period:12s}  {desc}")
            lines += ["```", ""]

            # 出典
            lines += ["### 出典・参照", ""]
            for ref_title, ref_url in d["refs"]:
                lines.append(f"- {ref_title}")
                lines.append(f"  {ref_url}")
            lines.append("")
        else:
            lines += [
                "### 解決する課題と目標年度",
                f"選択された施策「{title}」について詳細計画を策定します。",
                "",
                "### 実施アクション",
                "- 現状調査・要件定義",
                "- システム設計・開発",
                "- 導入・展開",
                "",
            ]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# デモ精緻化ビルダー
# ─────────────────────────────────────────────

def _build_demo_refine(
    municipality_name: str,
    instruction: str,
    future_vision: str,
    current_state: str = "",
    challenges: str = "",
    root_causes: str = "",
) -> str:
    """指示内容に応じてデモ提案書を精緻化する。"""
    low = instruction

    if "別案" in low or "別の" in low or "違う案" in low:
        # 代替施策セットで新しい提案書を生成
        measures = _ALT_DEMO_MEASURES
        intro = f"前回の提案とは異なるアプローチで、{municipality_name}に適した別の施策を提案します。"
    else:
        measures = _DEMO_MEASURES
        intro = f"ご指示「{instruction}」を踏まえ、提案書を更新しました。"

    lines: list[str] = [
        f"# {municipality_name} 地方創生DX提案書（更新版）",
        "",
        f"> {intro}",
        "",
        "## 実現したい将来像",
        future_vision or "（元の入力を継承）",
        "",
        "## 現状分析",
        "",
        "### 現在の状況",
        current_state or "（元の入力を継承）",
        "",
        "### 抱えている課題",
        challenges or "（元の入力を継承）",
        "",
        "### 課題の原因",
        root_causes or "（元の入力を継承）",
        "",
        "---",
        "",
        "## 提案する施策・ソリューション",
        "",
        "| 番号 | 施策名 | 優先度 | 概算費用 |",
        "|------|--------|--------|---------|",
    ]
    for _, num, title, priority, cost in measures:
        lines.append(f"| {num} | {title} | {priority} | {cost} |")
    lines.append("")

    lines += ["---", "", "## 提案する施策・ソリューションの個別具体", ""]

    for idx, num, title, _, cost in measures:
        d = _MEASURE_DETAILS.get(idx)
        lines += [f"### {num} {title}", "", "**概要**"]

        if "具体" in low or "詳し" in low:
            # より詳細な実装仕様を展開
            if d:
                lines.append(d["summary"])
                lines += ["", "**詳細実装要件**"]
                for f_item in d["features"]:
                    lines.append(f"- {f_item}")
                lines += [
                    "",
                    f"**推定効果（{municipality_name}・3年後）**",
                    "",
                    "| 指標 | 現状 | 1年後 | 3年後 |",
                    "|------|------|------|------|",
                ]
                for row in d["kpi"]:
                    lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |")
            else:
                lines.append(f"{title}の具体的な実装内容を拡充しました。")
        elif "コスト" in low or "予算" in low or "費用" in low:
            if d:
                lines.append(d["summary"])
                lines += [
                    "",
                    "**詳細コスト内訳**",
                    "",
                    "| 費目 | 金額 | 備考 |",
                    "|------|------|------|",
                ]
                for item, amount in d["estimate"]:
                    lines.append(f"| {item} | {amount} | 税込 |")
                lines += [
                    "",
                    "**コスト削減効果（3年累計試算）**",
                    f"- 本施策への投資: {cost}",
                    f"- 3年間の削減効果: 投資額の約2〜3倍相当",
                    "- 費用対効果: 投資回収期間 約2.5年（見込み）",
                ]
            else:
                lines.append(f"{title}の予算詳細を追加しました。")
        elif "スケジュール" in low or "期間" in low or "ロードマップ" in low:
            if d:
                lines.append(d["summary"])
                lines += ["", "**マスタースケジュール**", "", "```"]
                for period, desc in d["roadmap"]:
                    lines.append(f"{period:12s}  {desc}")
                lines += ["```", "", "**フェーズ別マイルストーン**"]
                lines.append("- Phase 1（〜6ヶ月）: 準備・設計")
                lines.append("- Phase 2（〜12ヶ月）: 開発・パイロット導入")
                lines.append("- Phase 3（〜24ヶ月）: 本格展開・効果測定")
            else:
                lines.append(f"{title}のスケジュール詳細を追加しました。")
        elif "事例" in low or "導入" in low:
            if d:
                lines.append(d["summary"])
                lines += ["", "**他自治体の導入事例**"]
                for ref_title, ref_url in d["refs"]:
                    lines.append(f"- {ref_title}")
                    lines.append(f"  参照: {ref_url}")
            else:
                lines.append(f"{title}の導入事例を追加しました。")
        elif "リスク" in low:
            if d:
                lines.append(d["summary"])
                lines += [
                    "",
                    "**リスクと対策**",
                    "",
                    "| リスク | 影響度 | 発生確率 | 対策 |",
                    "|--------|--------|----------|------|",
                    "| 住民の利用率が低迷 | 高 | 中 | 周知活動・サポート窓口の充実 |",
                    "| セキュリティインシデント | 高 | 低 | 定期的な脆弱性診断・ゼロトラスト設計 |",
                    "| ベンダーロックイン | 中 | 中 | 標準API採用・マルチベンダー戦略 |",
                    "| 職員の習熟不足 | 中 | 高 | 段階的ロールアウト・継続研修 |",
                ]
            else:
                lines.append(f"{title}のリスク分析を追加しました。")
        else:
            # 汎用：概要 + 見積もり
            if d:
                lines.append(d["summary"])
                lines += ["", "**主な内容**"]
                for f_item in d["features"]:
                    lines.append(f"- {f_item}")
            else:
                lines.append(f"{title}（{cost}）")

        lines += ["", "**見積もり**", "", "| 項目 | 金額 |", "|------|------|"]
        estimate = _MEASURE_DETAILS.get(idx, {}).get("estimate", [("概算合計", cost)])
        for item, amount in estimate:
            lines.append(f"| {item} | {amount} |")
        lines += ["", "---", ""]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# 公開 API
# ─────────────────────────────────────────────

async def generate_proposal(municipality_name: str, theme: str) -> str:
    """再生成等の旧 API 用（同期完了版）。"""
    if settings.APP_ENV == "demo":
        return _build_demo_proposal(
            municipality_name=municipality_name,
            future_vision=theme,
            current_state="",
            challenges="",
            root_causes="",
            url_contents=[],
            attachment_texts=[],
        )
    message = await _client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=8192,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"自治体名: {municipality_name}\n"
                    f"テーマ: {theme}\n\n"
                    "上記の自治体向けに、テーマに沿った地方創生DX提案書を作成してください。"
                ),
            }
        ],
    )
    first = message.content[0]
    return first.text if hasattr(first, "text") else ""


async def generate_proposal_streaming(
    municipality_name: str,
    future_vision: str,
    current_state: str = "",
    challenges: str = "",
    root_causes: str = "",
    url_contents: list[tuple[str, str]] | None = None,
    attachment_texts: list[tuple[str, str]] | None = None,
):
    """ストリーミングで初回提案書を生成する。SSE 用。"""
    import asyncio as _asyncio

    urls = url_contents or []
    files = attachment_texts or []

    if settings.APP_ENV == "demo":
        content = _build_demo_proposal(
            municipality_name=municipality_name,
            future_vision=future_vision,
            current_state=current_state,
            challenges=challenges,
            root_causes=root_causes,
            url_contents=urls,
            attachment_texts=files,
        )
        chunk_size = 30
        for i in range(0, len(content), chunk_size):
            yield content[i : i + chunk_size]
            await _asyncio.sleep(0.015)
        return

    user_content = (
        f"自治体名: {municipality_name}\n\n"
        f"【実現したい将来像】\n{future_vision}\n\n"
        f"【現在像】\n{current_state or '（未記入）'}\n\n"
        f"【抱えている課題】\n{challenges or '（未記入）'}\n\n"
        f"【課題の原因】\n{root_causes or '（未記入）'}\n"
    )
    if files:
        for fname, text in files:
            user_content += f"\n【添付資料: {fname}】\n{text[:5000]}\n"
    if urls:
        for url, content in urls:
            user_content += f"\n【参照URL: {url}】\n{content[:5000]}\n"
    user_content += "\n上記の情報をもとに、地方創生DX提案書を作成してください。"

    async with _client.messages.stream(
        model=settings.CLAUDE_MODEL,
        max_tokens=8192,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def generate_deepen_streaming(
    municipality_name: str,
    selected_measures: list[tuple[int, str]],
    future_vision: str = "",
):
    """選択された施策の詳細実施計画をストリーミングで生成する。"""
    import asyncio as _asyncio

    if settings.APP_ENV == "demo":
        content = _build_demo_deepen(
            municipality_name=municipality_name,
            selected_measures=selected_measures,
        )
        chunk_size = 30
        for i in range(0, len(content), chunk_size):
            yield content[i : i + chunk_size]
            await _asyncio.sleep(0.015)
        return

    measures_text = "\n".join(
        f"- 施策{i}: {title}" for i, title in selected_measures
    )
    user_content = (
        f"自治体名: {municipality_name}\n"
        f"将来像: {future_vision}\n\n"
        f"【採用する施策】\n{measures_text}\n\n"
        "上記の採用施策について、それぞれ詳細実施計画を作成してください。"
    )

    async with _client.messages.stream(
        model=settings.CLAUDE_MODEL,
        max_tokens=8192,
        system=_SYSTEM_DEEPEN_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def generate_refine_streaming(
    municipality_name: str,
    instruction: str,
    current_content: str = "",
    future_vision: str = "",
    current_state: str = "",
    challenges: str = "",
    root_causes: str = "",
):
    """AIへの追加指示で提案書を精緻化する。SSE 用。"""
    import asyncio as _asyncio

    if settings.APP_ENV == "demo":
        content = _build_demo_refine(
            municipality_name=municipality_name,
            instruction=instruction,
            future_vision=future_vision,
            current_state=current_state,
            challenges=challenges,
            root_causes=root_causes,
        )
        chunk_size = 30
        for i in range(0, len(content), chunk_size):
            yield content[i : i + chunk_size]
            await _asyncio.sleep(0.015)
        return

    user_content = (
        f"自治体名: {municipality_name}\n\n"
        f"【追加指示】\n{instruction}\n\n"
        f"【現在の提案書】\n{current_content[:6000]}\n\n"
        f"【元の入力情報】\n"
        f"将来像: {future_vision}\n"
        f"現在像: {current_state or '（未記入）'}\n"
        f"課題: {challenges or '（未記入）'}\n"
        f"原因: {root_causes or '（未記入）'}\n\n"
        "上記の追加指示を踏まえて、提案書を更新・改善してください。"
    )

    async with _client.messages.stream(
        model=settings.CLAUDE_MODEL,
        max_tokens=8192,
        system=_SYSTEM_REFINE_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        async for text in stream.text_stream:
            yield text
